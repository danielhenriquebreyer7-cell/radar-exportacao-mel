import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import io

import os
import datetime

def get_db_updated_time():
    try:
        timestamp = os.path.getmtime("mel_export.db")
        return datetime.datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y")
    except:
        return datetime.datetime.now().strftime("%d/%m/%Y")

# Configuração da página para um visual premium
st.set_page_config(page_title="Radar de Exportação: Mel Natural", layout="wide")

# ⚡ MENSAGEM DE CONFIRMAÇÃO - PODE REMOVER DEPOIS ⚡


# Estilo CSS customizado
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

def load_data():
    conn = sqlite3.connect("mel_export.db")
    df_br = pd.read_sql("SELECT * FROM exportacoes_mel", conn)
    try:
        df_global = pd.read_sql("SELECT * FROM comtrade_data", conn)
    except Exception:
        df_global = pd.DataFrame() # Tabela global pode não existir ainda

    try:
        df_bilateral = pd.read_sql("SELECT * FROM comtrade_bilateral", conn)
    except Exception:
        df_bilateral = pd.DataFrame()
        
    try:
        df_mensal = pd.read_sql("SELECT * FROM comtrade_mensal", conn)
    except Exception:
        df_mensal = pd.DataFrame()
        
    # FAO - Dados novos (download manual)
    try:
        df_fao_prod = pd.read_sql("SELECT * FROM fao_production_new", conn)
    except Exception:
        try:
            df_fao_prod = pd.read_sql("SELECT * FROM fao_production", conn)
        except Exception:
            df_fao_prod = pd.DataFrame()

    try:
        df_fao_price = pd.read_sql("SELECT * FROM fao_prices", conn)
    except Exception:
        df_fao_price = pd.DataFrame()
    
    try:
        df_fao_value = pd.read_sql("SELECT * FROM fao_value", conn)
    except Exception:
        df_fao_value = pd.DataFrame()
    
    try:
        df_fao_trade = pd.read_sql("SELECT * FROM fao_trade", conn)
    except Exception:
        df_fao_trade = pd.DataFrame()
    
    try:
        df_fao_indices = pd.read_sql("SELECT * FROM fao_indices", conn)
    except Exception:
        df_fao_indices = pd.DataFrame()

    try:
        df_ibge = pd.read_sql("SELECT * FROM ibge_ppm", conn)
    except Exception:
        df_ibge = pd.DataFrame()

    conn.close()
    return df_br, df_global, df_bilateral, df_mensal, df_fao_prod, df_fao_price, df_fao_value, df_fao_trade, df_fao_indices, df_ibge



def format_br(val, is_currency=False):
    """Formata números para o padrão brasileiro."""
    if pd.isna(val): return ""
    if is_currency:
        return f"US$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{val:,.0f}".replace(",", ".")

try:
    df, df_global, df_bilateral, df_mensal, df_fao_prod, df_fao_price, df_fao_value, df_fao_trade, df_fao_indices, df_ibge = load_data()
except Exception:
    st.error("Banco de dados não encontrado. Por favor, execute o processamento primeiro.")
    st.stop()
    


# Navegação Lateral
st.sidebar.title("Navegação")
view_mode = st.sidebar.radio("Selecione a Visão:", 
    ["Visão Brasil (Exportação)", "Visão Global (Mundo)", "Inteligência de Produção (FAO)", "Produção Interna (IBGE)"]
)

if view_mode == "Visão Brasil (Exportação)" or view_mode == "Visão Brasil (Local)":
    # --- CÓDIGO ORIGINAL DA VISÃO BRASIL ---
    st.sidebar.header("Filtros Brasil")
    anos = sorted(df['Ano'].unique(), reverse=True)
    selected_ano = st.sidebar.multiselect("Ano", anos, default=anos[:1])
    
    df_filtered = df[df['Ano'].isin(selected_ano)]
    
    ufs = sorted(df_filtered['UF'].unique()) if 'UF' in df_filtered.columns else []
    selected_uf = st.sidebar.multiselect("Estado (UF)", ufs)
    if selected_uf:
        df_filtered = df_filtered[df_filtered['UF'].isin(selected_uf)]
        
    # Filtro de Município
    municipios = sorted(df_filtered['Municipio'].unique())
    selected_mun = st.sidebar.multiselect("Município", municipios)
    if selected_mun:
        df_filtered = df_filtered[df_filtered['Municipio'].isin(selected_mun)]

    # Filtro de País de Destino
    paises = sorted(df_filtered['Pais'].unique())
    selected_pais = st.sidebar.multiselect("País Destino", paises)
    if selected_pais:
        df_filtered = df_filtered[df_filtered['Pais'].isin(selected_pais)]

    st.title("🍯 Radar de Exportação (Brasil): Mel Natural (SH4 0409)")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    total_usd = df_filtered['Valor_USD'].sum()
    total_kg = df_filtered['Peso_KG'].sum()
    avg_price = total_usd / total_kg if total_kg > 0 else 0
    
    with col1: st.metric("Total Exportado (US$ FOB)", format_br(total_usd, True))
    with col2: st.metric("Peso Líquido Total (KG)", f"{format_br(total_kg)} KG")
    with col3: st.metric("Preço Médio (USD/KG)", format_br(avg_price, True))
    
    st.markdown("---")
    

    # --- DIAGRAMA DE SANKEY (MUNICÍPIO -> PAÍS) ---
    st.subheader("🤝 Fluxo de Exportação: Município ➝ País (Quem vende para quem?)")

    if not df_filtered.empty:
        # Agrupar dados
        fluxo_br = df_filtered.groupby(['Municipio', 'Pais']).agg({
            'Valor_USD': 'sum',
            'Peso_KG': 'sum'
        }).reset_index()
        
        # Ordenar por valor e pegar top 50 (para performance e visualização)
        fluxo_br = fluxo_br.sort_values('Valor_USD', ascending=False).head(50)
        
        # Calcular métricas extras
        fluxo_br['Peso_Ton'] = fluxo_br['Peso_KG'] / 1000
        fluxo_br['Preco_Medio'] = fluxo_br['Valor_USD'] / fluxo_br['Peso_KG']
        
        # Criar nós do Sankey
        all_nodes = list(pd.concat([fluxo_br['Municipio'], fluxo_br['Pais']]).unique())
        node_map = {name: i for i, name in enumerate(all_nodes)}
        
        source_indices = fluxo_br['Municipio'].map(node_map).tolist()
        target_indices = fluxo_br['Pais'].map(node_map).tolist()
        values = fluxo_br['Valor_USD'].tolist()
        
        # Formatadores brasileiros
        fmt_usd = lambda x: f"US$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        fmt_ton = lambda x: f"{x:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        custom_v = fluxo_br['Valor_USD'].apply(fmt_usd).tolist()
        custom_w = fluxo_br['Peso_Ton'].apply(fmt_ton).tolist()
        custom_p = fluxo_br['Preco_Medio'].apply(fmt_usd).tolist() # Reutiliza fmt_usd pois é moeda
        
        # Zipar para customdata
        custom_data_zipped = list(zip(custom_v, custom_w, custom_p))
        
        import plotly.graph_objects as go
        
        fig_sankey_br = go.Figure(data=[go.Sankey(
            textfont={'size': 12, 'color': 'black'},
            node = dict(
                pad = 15,
                thickness = 20,
                line = dict(color = "black", width = 0.5),
                label = all_nodes,
                color = "orange" # Laranja solicitado pelo usuário
            ),
            link = dict(
                source = source_indices,
                target = target_indices,
                value = values,
                customdata = custom_data_zipped,
                hovertemplate='<b>%{source.label}</b> ➝ <b>%{target.label}</b><br>' +
                              'Valor: %{customdata[0]}<br>' +
                              'Peso: %{customdata[1]} Ton<br>' +
                              'Preço Médio: %{customdata[2]}/kg<extra></extra>'
            )
        )])
        
        fig_sankey_br.update_layout(
            title_text=f"Top {len(fluxo_br)} Rotas Comerciais (USD)", 
            font_size=12, 
            height=700,
            separators=",."
        )
        st.plotly_chart(fig_sankey_br, use_container_width=True)
    else:
        st.info("Sem dados suficientes para gerar o diagrama de fluxo.")

    st.markdown("---")

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.subheader("Destinos Principais (US$ FOB)")
        if not df_filtered.empty:
            df_filtered['Pais'] = df_filtered['Pais'].astype(str)
            destinos = df_filtered.groupby('Pais').agg({
                'Valor_USD': 'sum',
                'Peso_KG': 'sum'
            }).reset_index()
            destinos['Preco_Medio'] = destinos['Valor_USD'] / destinos['Peso_KG']
            destinos = destinos.sort_values('Valor_USD', ascending=False).head(10)
            
            fig_destinos = px.bar(destinos, x='Valor_USD', y='Pais', orientation='h', 
                                  color='Valor_USD', color_continuous_scale='YlOrBr',
                                  custom_data=['Peso_KG', 'Preco_Medio'])
                                  
            fig_destinos.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, separators=",.")
            fig_destinos.update_traces(
                hovertemplate="<b>%{y}</b><br>Valor: US$ %{x:,.2f}<br>Peso: %{customdata[0]:,.0f} KG<br>Preço Médio: US$ %{customdata[1]:,.2f}<extra></extra>"
            )
            st.plotly_chart(fig_destinos, use_container_width=True)
        else:
            st.info("Sem dados.")
            
    with row1_col2:
        st.subheader("Municípios Exportadores (KG)")
        if not df_filtered.empty:
            df_filtered['Municipio'] = df_filtered['Municipio'].astype(str)
            muns = df_filtered.groupby('Municipio').agg({
                'Valor_USD': 'sum',
                'Peso_KG': 'sum'
            }).reset_index()
            muns['Preco_Medio'] = muns['Valor_USD'] / muns['Peso_KG']
            muns = muns.sort_values('Peso_KG', ascending=False).head(10)
            
            fig_muns = px.bar(muns, x='Peso_KG', y='Municipio', orientation='h', 
                              color='Peso_KG', color_continuous_scale='Blues',
                              custom_data=['Valor_USD', 'Preco_Medio'])
                              
            fig_muns.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, separators=",.")
            fig_muns.update_traces(
                hovertemplate="<b>%{y}</b><br>Peso: %{x:,.0f} KG<br>Valor: US$ %{customdata[0]:,.2f}<br>Preço Médio: US$ %{customdata[1]:,.2f}<extra></extra>"
            )
            st.plotly_chart(fig_muns, use_container_width=True)
        else:
            st.info("Sem dados.")

    st.markdown("---")
    
    st.subheader("📈 Evolução Temporal (KG)")
    if not df_filtered.empty:
        evolucao = df_filtered.groupby(['Ano', 'Mes', 'Mes_Num'])['Peso_KG'].sum().reset_index()
        evolucao = evolucao.sort_values(['Ano', 'Mes_Num'])
        fig_evolucao = px.line(evolucao, x='Mes', y='Peso_KG', color='Ano', markers=True)
        fig_evolucao.update_layout(separators=",.", hovermode="x unified")
        fig_evolucao.update_traces(hovertemplate='<b>%{y:,.0f} KG</b>')
        st.plotly_chart(fig_evolucao, use_container_width=True)
    else:
        st.info("Sem dados para o período selecionado.")

    # --- Tabela Detalhada Restaurada ---
    st.markdown("---")
    st.subheader("📋 Relatório Detalhado")
    
    if not df_filtered.empty:
        df_display = df_filtered.sort_values(['Ano', 'Mes_Num'], ascending=[False, False]).copy()
        
        # Ajuste para ordenação correta: adicionar prefixo numérico (ex: "01 - Janeiro")
        df_display['Mes'] = df_display['Mes_Num'].astype(str).str.zfill(2) + ' - ' + df_display['Mes'].astype(str)
        
        # Adicionar Preço Médio
        df_display['Preco_Medio'] = df_display['Valor_USD'] / df_display['Peso_KG']
        
        # Colunas finais
        colunas_finais = ['Ano', 'Mes', 'Municipio', 'UF', 'Pais', 'Valor_USD', 'Peso_KG', 'Preco_Medio']
        df_display = df_display[colunas_finais]

        # Botão Download Excel
        output = io.BytesIO()
        df_excel = df_display.copy()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_excel.to_excel(writer, index=False, sheet_name='Exportacoes_Mel')
        
        st.download_button(
            label="📥 Baixar Tabela em Excel (.xlsx)",
            data=output.getvalue(),
            file_name=f"exportacoes_mel_detalhado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Tabela Formatada
        st.dataframe(
            df_display.style.format({
                'Valor_USD': lambda x: f"US$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                'Peso_KG': lambda x: f"{x:,.0f}".replace(",", ".") + " KG",
                'Preco_Medio': lambda x: f"US$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            }), 
            use_container_width=True
        )
    else:
        st.info("Nenhum dado para exibir na tabela.")
    
    
    st.markdown("---")
    st.markdown(f"<div style='text-align: right; color: #666; font-size: 0.8em;'>Atualizado da fonte: MDIC / Comex Stat em {get_db_updated_time()}</div>", unsafe_allow_html=True)

elif view_mode == "Visão Global (Mundo)":
    # --- VISÃO GLOBAL (COMTRADE) ---
    st.sidebar.header("Filtros Global")
    if not df_global.empty:
        # 1. Filtro de Ano
        anos_global = sorted(df_global['Ano'].unique(), reverse=True)
        selected_ano_g = st.sidebar.multiselect("Ano", anos_global, default=anos_global[:1])
        
        # 2. Filtro de Países (Opcional - para ver performance específica)
        paises_global = sorted(df_global['Pais'].unique())
        selected_pais_g = st.sidebar.multiselect("Países de Interesse", paises_global)

        df_g_filtered = df_global[df_global['Ano'].isin(selected_ano_g)]
        if selected_pais_g:
            df_g_filtered = df_g_filtered[df_g_filtered['Pais'].isin(selected_pais_g)]
        
        st.title("🌍 Radar Global: Exportadores e Importadores")
        st.markdown(f"**Fonte:** UN Comtrade | **Anos:** {', '.join(map(str, selected_ano_g))}")
        
        # --- NOVO: DIAGRAMA DE SANKEY (FLOW) ---
        # Filtrar bilateral também
        df_bil_filtered = pd.DataFrame()
        if not df_bilateral.empty:
            df_bil_filtered = df_bilateral[df_bilateral['Ano'].isin(selected_ano_g)]
            
            if selected_pais_g:
                 df_bil_filtered = df_bil_filtered[
                     df_bil_filtered['Origem'].isin(selected_pais_g) | 
                     df_bil_filtered['Destino'].isin(selected_pais_g)
                 ]

        if not df_bil_filtered.empty:
            st.markdown("---")
            st.subheader("🤝 Quem Vende para Quem? (Diagrama de Fluxo)")
            
            # Limitar para não travar o navegador: Top 40 maiores fluxos
            top_flows = df_bil_filtered.sort_values('Valor_USD', ascending=False).head(40)
            
            if not top_flows.empty:
                # Sankey precisa de índices numéricos para Source e Target
                all_nodes = list(pd.concat([top_flows['Origem'], top_flows['Destino']]).unique())
                node_map = {name: i for i, name in enumerate(all_nodes)}
                
                source_indices = top_flows['Origem'].map(node_map).tolist()
                target_indices = top_flows['Destino'].map(node_map).tolist()
                values = top_flows['Valor_USD'].tolist()
                
                import plotly.graph_objects as go
                
                fig_sankey = go.Figure(data=[go.Sankey(
                    textfont={'size': 12, 'color': 'black'},
                    node = dict(
                        pad = 15,
                        thickness = 20,
                        line = dict(color = "black", width = 0.5),
                        label = all_nodes,
                        color = "blue"
                    ),
                    link = dict(
                        source = source_indices,
                        target = target_indices,
                        value = values,
                        hovertemplate='<b>%{source.label}</b> partiu para <b>%{target.label}</b><br>Valor: US$ %{value:,.2f}<extra></extra>'
                    )
                )])
                
                fig_sankey.update_layout(title_text=f"Top {len(top_flows)} Maiores Fluxos Comerciais (USD)", font_size=12, height=600, separators=",.")
                st.plotly_chart(fig_sankey, use_container_width=True)
                
                with st.expander("Ver Detalhes dos Fluxos"):
                    # Cálculos e Formatação para Tabela Bilateral
                    top_flows['Preco_Medio'] = top_flows['Valor_USD'] / top_flows['Peso_KG']
                    
                    fmt_usd = lambda x: f"US$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    fmt_kg = lambda x: f"{x:,.0f}".replace(",", ".") + " KG"
                    
                    cols_bilateral = ['Ano', 'Origem', 'Destino', 'Valor_USD', 'Peso_KG', 'Preco_Medio']
                    st.dataframe(top_flows[cols_bilateral].style.format({
                        'Valor_USD': fmt_usd, 
                        'Peso_KG': fmt_kg,
                        'Preco_Medio': fmt_usd
                    }), use_container_width=True)
            else:
                 st.info("Sem dados bilaterais suficientes para o gráfico.")

        st.markdown("---")
        
        # --- NOVO: SAZONALIDADE (MENSAL) ---
        if not df_mensal.empty:
            st.markdown("---")
            st.subheader("📅 Sazonalidade do Comércio Global")
            # Filtros aplicados ao mensal
            df_m_filtered = df_mensal[df_mensal['Ano'].isin(selected_ano_g)]
            if selected_pais_g:
                df_m_filtered = df_m_filtered[df_m_filtered['Pais'].isin(selected_pais_g)]
            
            if not df_m_filtered.empty:
                # Agrupar por Mes e Tipo
                sazonal = df_m_filtered.groupby(['Mes', 'Tipo'])['Valor_USD'].sum().reset_index()
                
                # Mapear nome do mês
                MONTH_MAP = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun',
                             7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
                sazonal['Mes_Nome'] = sazonal['Mes'].map(MONTH_MAP)
                
                fig_saz = px.line(
                    sazonal, 
                    x='Mes_Nome', 
                    y='Valor_USD', 
                    color='Tipo', 
                    markers=True,
                    title="Evolução Mensal: Exportações vs Importações (USD)",
                    labels={'Valor_USD': 'Valor (USD)', 'Mes_Nome': 'Mês'},
                    color_discrete_map={'Export': '#1f77b4', 'Import': '#ff7f0e'}
                )
                # Formatar Eixo Y BR
                fig_saz.update_layout(yaxis_tickformat=",.2f", separators=",.") 
                st.plotly_chart(fig_saz, use_container_width=True)
            else:
                st.info("Sem dados mensais para os filtros selecionados.")

        st.markdown("---")

        # Separar Exportação e Importação
        df_exports = df_g_filtered[df_g_filtered['Tipo'] == 'Export']
        df_imports = df_g_filtered[df_g_filtered['Tipo'] == 'Import']

        # --- GRÁFICO 1: TOP 10 EXPORTADORES ---
        st.subheader("🚢 Top 10 Maiores Exportadores")
        
        if not df_exports.empty:
            ranking_exp = df_exports.groupby('Pais').agg({
                'Valor_USD': 'sum',
                'Peso_KG': 'sum'
            }).reset_index()
            
            # Calcular preço médio
            ranking_exp['Preco_Medio'] = ranking_exp['Valor_USD'] / ranking_exp['Peso_KG']
            
            # Sort e Top 10
            ranking_exp = ranking_exp.sort_values('Valor_USD', ascending=False).head(10)
            
            # Destacar Brasil se estiver no ranking
            ranking_exp['Color'] = ranking_exp['Pais'].apply(lambda x: '#009c3b' if 'Brazil' in str(x) or 'Brasil' in str(x) else '#1f77b4')

            # Preparar textos formatados para o Tooltip (Plotly tem dificuldade com locale pt-BR nativo)
            fmt_usd = lambda x: f"US$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            fmt_kg = lambda x: f"{x:,.0f}".replace(",", ".") + " KG"
            
            ranking_exp['Valor_FMT'] = ranking_exp['Valor_USD'].apply(fmt_usd)
            ranking_exp['Peso_FMT'] = ranking_exp['Peso_KG'].apply(fmt_kg)
            ranking_exp['Preco_FMT'] = ranking_exp['Preco_Medio'].apply(fmt_usd)

            fig_exp = px.bar(
                ranking_exp, 
                x='Valor_USD', 
                y='Pais', 
                orientation='h',
                title="Quem mais VENDE mel no mundo (USD)",
                color='Color',
                color_discrete_map='identity',
                # Passamos os dados formatados como custom_data
                custom_data=['Valor_FMT', 'Peso_FMT', 'Preco_FMT']
            )
            
            fig_exp.update_traces(
                hovertemplate="<b>%{y}</b><br>Valor: %{customdata[0]}<br>Peso: %{customdata[1]}<br>Preço Médio: %{customdata[2]}/kg<extra></extra>"
            )
            fig_exp.update_layout(
                yaxis={'categoryorder':'total ascending'}, 
                showlegend=False,
                xaxis_title="Valor Exportado (USD)",
                separators=",."
            )
            st.plotly_chart(fig_exp, use_container_width=True)
            
            with st.expander("Ver Tabela Detalhada (Exportadores)"):
                # Mostrar colunas relevantes (ocultar Color e Formats auxiliares)
                cols_to_show = ['Pais', 'Valor_USD', 'Peso_KG', 'Preco_Medio']
                st.dataframe(ranking_exp[cols_to_show].style.format({
                    'Valor_USD': fmt_usd, 
                    'Peso_KG': fmt_kg, 
                    'Preco_Medio': fmt_usd
                }), use_container_width=True)
        else:
            st.info("Sem dados de exportação para filtros selecionados.")
        


        # --- GRÁFICO 2: TOP 10 IMPORTADORES ---
        st.subheader("🛒 Top 10 Maiores Importadores (Mercados-Alvo)")
        
        if not df_imports.empty:
            ranking_imp = df_imports.groupby('Pais').agg({
                'Valor_USD': 'sum',
                'Peso_KG': 'sum'
            }).reset_index()
            
            ranking_imp['Preco_Medio'] = ranking_imp['Valor_USD'] / ranking_imp['Peso_KG']
            ranking_imp = ranking_imp.sort_values('Valor_USD', ascending=False).head(10)
            
            # Formatadores locais para este bloco
            fmt_usd = lambda x: f"US$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            fmt_kg = lambda x: f"{x:,.0f}".replace(",", ".") + " KG"
            
            ranking_imp['Valor_FMT'] = ranking_imp['Valor_USD'].apply(fmt_usd)
            ranking_imp['Peso_FMT'] = ranking_imp['Peso_KG'].apply(fmt_kg)
            ranking_imp['Preco_FMT'] = ranking_imp['Preco_Medio'].apply(fmt_usd)
            
            # Gráfico Importadores
            fig_imp = px.bar(
                ranking_imp, 
                x='Valor_USD', 
                y='Pais', 
                orientation='h',
                title="Quem mais COMPRA mel no mundo (USD)",
                color_discrete_sequence=['#ff7f0e'],
                custom_data=['Valor_FMT', 'Peso_FMT', 'Preco_FMT']
            )
            
            fig_imp.update_traces(
                hovertemplate="<b>%{y}</b><br>Valor: %{customdata[0]}<br>Peso: %{customdata[1]}<br>Preço Médio: %{customdata[2]}/kg<extra></extra>"
            )
            fig_imp.update_layout(
                yaxis={'categoryorder':'total ascending'},
                xaxis_title="Valor Importado (USD)",
                separators=",."
            )
            st.plotly_chart(fig_imp, use_container_width=True)

            with st.expander("Ver Tabela Detalhada (Importadores)"):
                 cols_to_show = ['Pais', 'Valor_USD', 'Peso_KG', 'Preco_Medio']
                 st.dataframe(ranking_imp[cols_to_show].style.format({
                    'Valor_USD': fmt_usd, 
                    'Peso_KG': fmt_kg, 
                    'Preco_Medio': fmt_usd
                }), use_container_width=True)
        else:
            st.info("Sem dados de importação para filtros selecionados.")
        
    else:
        st.warning("Dados globais (Comtrade) ainda não disponíveis. Execute a importação primeiro.")

    
    st.markdown("---")
    st.markdown(f"<div style='text-align: right; color: #666; font-size: 0.8em;'>Atualizado da fonte: UN Comtrade em {get_db_updated_time()}</div>", unsafe_allow_html=True)

elif view_mode == "Inteligência de Produção (FAO)":
    st.title("🌍 Produção Global de Mel (FAOSTAT)")
    st.markdown("**Fonte:** FAO | **Dados:** Produção, Colmeias, Preços ao Produtor | **Período:** Últimos 3 anos")
    st.markdown("---")

    if df_fao_prod.empty:
        st.warning("Dados FAO não disponíveis. Execute o processamento primeiro.")
    else:
        # Funções de formatação BR
        fmt_kg = lambda x: f"{x:,.0f}".replace(",", ".") + " kg"
        fmt_num = lambda x: f"{x:,.0f}".replace(",", ".")
        fmt_dec = lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        fmt_usd = lambda x: f"US$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        # Sidebar: Filtro de Ano
        st.sidebar.header("Filtros FAO")
        anos_disp = sorted(df_fao_prod['Ano'].dropna().unique(), reverse=True)
        sel_ano = st.sidebar.selectbox("Ano de Referência", anos_disp, index=0)
        
        # Filtrar dados pelo ano selecionado
        prod_ano = df_fao_prod[df_fao_prod['Ano'] == sel_ano].copy()
        price_ano = df_fao_price[df_fao_price['Ano'] == sel_ano].copy() if not df_fao_price.empty else pd.DataFrame()
        
        # ===== MÉTRICAS GLOBAIS =====
        total_prod_kg = prod_ano['Producao_Kg'].sum()
        
        # Colmeias podem não existir nos novos dados
        has_colmeias = 'Colmeias' in prod_ano.columns and prod_ano['Colmeias'].notna().any()
        total_colmeias = prod_ano['Colmeias'].sum() if has_colmeias else 0
        produtividade_global = total_prod_kg / total_colmeias if total_colmeias > 0 else 0
        
        # Preço Médio (Exportação) - Fonte: FAO Trade (fao_trade)
        # Se disponível, calculamos preço médio de exportação (Valor / Qty)
        preco_medio_kg = 0
        if not df_fao_trade.empty:
            trade_metrics = df_fao_trade[df_fao_trade['Ano'] == sel_ano]
            total_exp_val = trade_metrics['Export_Value_1000USD'].sum() * 1000
            total_exp_qty = trade_metrics['Export_Qty_Ton'].sum() * 1000
            if total_exp_qty > 0:
                preco_medio_kg = total_exp_val / total_exp_qty
        
        # Fallback para tabela de preços antiga se necessário (mas evitar se for ruim)
        if preco_medio_kg == 0 and not price_ano.empty and 'Preco_USD_Kg' in price_ano.columns:
             preco_medio_kg = price_ano['Preco_USD_Kg'].mean()

        # Número de países com produção
        num_paises = prod_ano['Pais'].nunique()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"Produção Global ({sel_ano})", fmt_kg(total_prod_kg))
        c2.metric("Países Produtores", fmt_num(num_paises))
        if has_colmeias and total_colmeias > 0:
            c3.metric("Produtividade Média", f"{fmt_dec(produtividade_global)} kg/colmeia")
        else:
            # Média por país como alternativa
            media_pais = total_prod_kg / num_paises if num_paises > 0 else 0
            c3.metric("Média por País", fmt_kg(media_pais))
            
        label_preco = "Preço Médio (Exportação)" if not df_fao_trade.empty else "Preço Médio (Produtor)"
        c4.metric(label_preco, f"US$ {fmt_dec(preco_medio_kg)}/kg" if preco_medio_kg > 0 else "N/D")
        
        st.markdown("---")
        
        # ===== TOP 15 PRODUTORES + CARD BRASIL =====
        col_chart, col_brasil = st.columns([2, 1])
        
        with col_chart:
            st.subheader("🏆 Top 15 Maiores Produtores")
            top15 = prod_ano.nlargest(15, 'Producao_Kg').copy()
            top15['Cor'] = top15['Pais'].apply(lambda x: '#009c3b' if 'Brazil' in str(x) else '#1f77b4')
            
            fig_top15 = px.bar(
                top15, 
                x='Producao_Kg', 
                y='Pais', 
                orientation='h',
                text=top15['Producao_Kg'].apply(lambda x: f"{x/1e6:.1f}M kg"),
                color='Cor',
                color_discrete_map='identity'
            )
            fig_top15.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                separators=",.",
                showlegend=False,
                xaxis_title="Produção (kg)",
                yaxis_title=""
            )
            fig_top15.update_traces(textposition='outside')
            st.plotly_chart(fig_top15, use_container_width=True)
        
        with col_brasil:
            st.subheader("🇧🇷 Posição do Brasil")
            
            # Calcular ranking do Brasil
            prod_ranking = prod_ano.sort_values('Producao_Kg', ascending=False).reset_index(drop=True)
            prod_ranking['Ranking'] = range(1, len(prod_ranking) + 1)
            
            brasil = prod_ranking[prod_ranking['Pais'].str.contains('Brazil', na=False)]
            
            if not brasil.empty:
                br = brasil.iloc[0]
                st.metric("Ranking Mundial", f"#{int(br['Ranking'])}º")
                st.metric("Produção", fmt_kg(br['Producao_Kg']))
                if has_colmeias and 'Colmeias' in br.index and pd.notna(br.get('Colmeias', None)):
                    st.metric("Colmeias", fmt_num(br['Colmeias']))
                if 'Produtividade_Kg' in br.index and pd.notna(br.get('Produtividade_Kg', None)):
                    st.metric("Produtividade", f"{fmt_dec(br['Produtividade_Kg'])} kg/col")
                # Participação no mercado global
                share = (br['Producao_Kg'] / total_prod_kg * 100) if total_prod_kg > 0 else 0
                st.metric("Participação Global", f"{share:.1f}%")
            else:
                st.info("Brasil não encontrado nos dados do período.")
        
        st.markdown("---")
        
        # ===== EVOLUÇÃO 3 ANOS: BRASIL vs TOP 5 =====
        st.subheader("📈 Evolução da Produção (3 Anos)")
        
        # Top 5 do último ano + Brasil
        top5_paises = prod_ano.nlargest(5, 'Producao_Kg')['Pais'].tolist()
        if 'Brazil' not in top5_paises:
            paises_evolucao = top5_paises + ['Brazil']
        else:
            paises_evolucao = top5_paises
        
        df_evolucao = df_fao_prod[df_fao_prod['Pais'].isin(paises_evolucao)].copy()
        df_evolucao = df_evolucao.sort_values('Ano')
        
        if not df_evolucao.empty:
            fig_evolucao = px.line(
                df_evolucao,
                x='Ano',
                y='Producao_Kg',
                color='Pais',
                markers=True,
                labels={'Producao_Kg': 'Produção (kg)', 'Ano': 'Ano'}
            )
            fig_evolucao.update_layout(separators=",.", legend_title="País")
            st.plotly_chart(fig_evolucao, use_container_width=True)
        else:
            st.info("Dados insuficientes para evolução.")
        
        st.markdown("---")
        
        # ===== PRODUTIVIDADE: COLMEIAS vs PRODUTIVIDADE =====
        # Só mostrar se temos dados de colmeias
        if has_colmeias and 'Produtividade_Kg' in prod_ano.columns:
            st.subheader("🐝 Análise de Produtividade (Colmeias vs Kg/Colmeia)")
            st.caption("Tamanho = Produção Total | Cor = Produtividade")
            
            # Filtrar países com dados válidos (mín. 1000 colmeias para evitar outliers)
            df_produtividade = prod_ano[(prod_ano['Colmeias'] > 1000) & (prod_ano['Produtividade_Kg'] > 0)].copy()
        
            if not df_produtividade.empty:
                # Destacar Brasil
                df_produtividade['E_Brasil'] = df_produtividade['Pais'].str.contains('Brazil', na=False)
                
                fig_scatter = px.scatter(
                    df_produtividade,
                    x='Colmeias',
                    y='Produtividade_Kg',
                    size='Producao_Kg',
                    color='Produtividade_Kg',
                    hover_name='Pais',
                    hover_data={
                        'Colmeias': ':,.0f',
                        'Produtividade_Kg': ':.1f',
                        'Producao_Kg': ':,.0f'
                    },
                    labels={
                        'Colmeias': 'Nº de Colmeias',
                        'Produtividade_Kg': 'Produtividade (kg/colmeia)',
                        'Producao_Kg': 'Produção (kg)'
                    },
                    color_continuous_scale='Viridis'
                )
                fig_scatter.update_layout(separators=",.")
                
                # Marcar Brasil com borda
                brasil_data = df_produtividade[df_produtividade['E_Brasil']]
                if not brasil_data.empty:
                    fig_scatter.add_scatter(
                        x=brasil_data['Colmeias'],
                        y=brasil_data['Produtividade_Kg'],
                        mode='markers',
                        marker=dict(size=20, color='rgba(0,0,0,0)', line=dict(color='#009c3b', width=3)),
                        name='Brasil',
                        showlegend=True
                    )
                
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("Dados insuficientes para análise de produtividade.")
        
        # ===== COMÉRCIO GLOBAL (FAO) =====
        if not df_fao_trade.empty:
            st.markdown("---")
            st.subheader("🌐 Balança Comercial Global (FAO)")
            
            trade_ano = df_fao_trade[df_fao_trade['Ano'] == sel_ano].copy()
            
            if not trade_ano.empty:
                # Top 15 maiores exportadores líquidos
                trade_ano = trade_ano.sort_values('Balanca_1000USD', ascending=False)
                
                col_exp, col_imp = st.columns(2)
                
                with col_exp:
                    st.markdown("##### 🚢 Maiores Exportadores Líquidos")
                    top_exporters = trade_ano.head(10).copy()
                    top_exporters['Cor'] = top_exporters['Pais'].apply(lambda x: '#009c3b' if 'Brazil' in str(x) else '#2ecc71')
                    
                    fig_exp = px.bar(
                        top_exporters,
                        x='Balanca_1000USD',
                        y='Pais',
                        orientation='h',
                        color='Cor',
                        color_discrete_map='identity',
                        labels={'Balanca_1000USD': 'Saldo (1000 USD)', 'Pais': ''}
                    )
                    fig_exp.update_layout(
                        yaxis={'categoryorder': 'total ascending'},
                        showlegend=False,
                        separators=",."
                    )
                    st.plotly_chart(fig_exp, use_container_width=True)
                
                with col_imp:
                    st.markdown("##### 🛒 Maiores Importadores Líquidos")
                    top_importers = trade_ano.tail(10).sort_values('Balanca_1000USD').copy()
                    top_importers['Cor'] = '#e74c3c'
                    
                    fig_imp = px.bar(
                        top_importers,
                        x='Balanca_1000USD',
                        y='Pais',
                        orientation='h',
                        color='Cor',
                        color_discrete_map='identity',
                        labels={'Balanca_1000USD': 'Saldo (1000 USD)', 'Pais': ''}
                    )
                    fig_imp.update_layout(
                        yaxis={'categoryorder': 'total descending'},
                        showlegend=False,
                        separators=",."
                    )
                    st.plotly_chart(fig_imp, use_container_width=True)
        
        # ===== VALOR DA PRODUÇÃO =====
        if not df_fao_value.empty:
            st.markdown("---")
            st.subheader("💰 Valor da Produção Agrícola (FAO)")
            
            value_ano = df_fao_value[df_fao_value['Ano'] == sel_ano].copy()
            
            if not value_ano.empty:
                # Top 15 por valor
                top_value = value_ano.nlargest(15, 'Valor_1000_IntDollar').copy()
                top_value['Cor'] = top_value['Pais'].apply(lambda x: '#009c3b' if 'Brazil' in str(x) else '#3498db')
                
                fig_value = px.bar(
                    top_value,
                    x='Valor_1000_IntDollar',
                    y='Pais',
                    orientation='h',
                    text=top_value['Valor_1000_IntDollar'].apply(lambda x: f"${x/1000:.1f}M"),
                    color='Cor',
                    color_discrete_map='identity',
                    labels={'Valor_1000_IntDollar': 'Valor (1000 Int$)', 'Pais': ''}
                )
                fig_value.update_layout(
                    yaxis={'categoryorder': 'total ascending'},
                    showlegend=False,
                    separators=",.",
                    title=f"Top 15 - Valor Bruto da Produção de Mel ({sel_ano})"
                )
                fig_value.update_traces(textposition='outside')
                st.plotly_chart(fig_value, use_container_width=True)
        
        # ===== TABELA DETALHADA =====
        with st.expander("📊 Ver Tabela Completa"):
            # Merge com preços se disponível
            if not price_ano.empty:
                df_tabela = pd.merge(prod_ano, price_ano[['Pais', 'Preco_USD_Kg']], on='Pais', how='left')
            else:
                df_tabela = prod_ano.copy()
                df_tabela['Preco_USD_Kg'] = None
            
            df_tabela = df_tabela.sort_values('Producao_Kg', ascending=False)
            
            # Formatar colunas
            colunas_show = ['Pais', 'Producao_Kg']
            if 'Colmeias' in df_tabela.columns:
                colunas_show.append('Colmeias')
            if 'Produtividade_Kg' in df_tabela.columns:
                colunas_show.append('Produtividade_Kg')
            if 'Preco_USD_Kg' in df_tabela.columns:
                colunas_show.append('Preco_USD_Kg')
            
            format_dict = {'Producao_Kg': '{:,.0f}'}
            if 'Colmeias' in colunas_show:
                format_dict['Colmeias'] = '{:,.0f}'
            if 'Produtividade_Kg' in colunas_show:
                format_dict['Produtividade_Kg'] = '{:,.1f}'
            if 'Preco_USD_Kg' in colunas_show:
                format_dict['Preco_USD_Kg'] = 'US$ {:,.2f}'
            

            st.dataframe(
                df_tabela[colunas_show].style.format(format_dict, na_rep='-'),
                use_container_width=True
            )
            
    st.markdown("---")
    st.markdown(f"<div style='text-align: right; color: #666; font-size: 0.8em;'>Atualizado da fonte: FAOSTAT em {get_db_updated_time()}</div>", unsafe_allow_html=True)


st.sidebar.markdown("---")

# --- VISÃO IBGE (Produção Interna) ---
if view_mode == "Produção Interna (IBGE)":
    st.title("🇧🇷 Produção Nacional de Mel (IBGE)")
    st.markdown("**Fonte:** IBGE (Pesquisa da Pecuária Municipal - PPM) | **Atualização:** Anual")
    st.markdown("---")

    if df_ibge.empty:
        st.warning("Dados do IBGE ainda não disponíveis. Aguarde o término da importação.")
    else:
        # Mapa de UF ID para Sigla
        UF_MAP = {
            11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO',
            21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA',
            31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP',
            41: 'PR', 42: 'SC', 43: 'RS',
            50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'
        }
        
        # Enriquecer dataset com Sigla UF se não existir
        if 'UF_Sigla' not in df_ibge.columns:
            df_ibge['UF_Sigla'] = df_ibge['UF_ID'].map(UF_MAP)

        # Filtros Sidebar
        st.sidebar.header("Filtros IBGE")
        
        # Ano
        anos_ibge = sorted(df_ibge['Ano'].unique(), reverse=True)
        sel_ano_ibge = st.sidebar.selectbox("Ano", anos_ibge)
        
        # Filtrar por ano primeiro
        df_ibge_ano = df_ibge[df_ibge['Ano'] == sel_ano_ibge].copy()
        
        # Estado
        ufs_disp = sorted(df_ibge_ano['UF_Sigla'].dropna().unique())
        sel_uf_ibge = st.sidebar.multiselect("Estado (UF)", ufs_disp)
        
        if sel_uf_ibge:
            df_ibge_ano = df_ibge_ano[df_ibge_ano['UF_Sigla'].isin(sel_uf_ibge)]
            
        # Município (dependente do estado)
        muns_disp = sorted(df_ibge_ano['Municipio'].unique())
        sel_mun_ibge = st.sidebar.multiselect("Município", muns_disp)
        
        if sel_mun_ibge:
            df_ibge_ano = df_ibge_ano[df_ibge_ano['Municipio'].isin(sel_mun_ibge)]
            
        # --- KPIs ---
        total_prod = df_ibge_ano['Producao_Kg'].sum()
        total_valor = df_ibge_ano['Valor_Prod_MilReais'].sum() * 1000 # Converter para Reais
        
        if total_prod > 0:
            preco_medio = total_valor / total_prod
        else:
            preco_medio = 0
            
        col1, col2, col3 = st.columns(3)
        col1.metric("Produção Total", f"{total_prod:,.0f}".replace(",", ".") + " kg")
        col2.metric("Valor Total da Produção", f"R$ {total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col3.metric("Preço Médio Implícito", f"R$ {preco_medio:,.2f} / kg")
        
        st.markdown("---")
        
        # --- TURBO: Gráficos ---
        
        c_chart1, c_chart2 = st.columns(2)
        
        with c_chart1:
            st.subheader("🏆 Principais Estados Produtores")
            # Agrupar por UF
            by_uf = df_ibge_ano.groupby('UF_Sigla')[['Producao_Kg', 'Valor_Prod_MilReais']].sum().reset_index()
            by_uf = by_uf.sort_values('Producao_Kg', ascending=False).head(10)
            
            # Cor para destacar top 1
            by_uf['Color'] = ['#009c3b'] + ['#1f77b4']*(len(by_uf)-1)

            fig_uf = px.bar(
                by_uf,
                x='Producao_Kg',
                y='UF_Sigla',
                orientation='h',
                text=by_uf['Producao_Kg'].apply(lambda x: f"{x/1e3:.1f}k"),
                title=f"Top 10 Estados em {sel_ano_ibge}",
                labels={'Producao_Kg': 'Produção (kg)', 'UF_Sigla': 'UF'},
                color='Color',
                color_discrete_map='identity'
            )
            fig_uf.update_layout(yaxis={'categoryorder': 'total ascending'}, separators=",.")
            st.plotly_chart(fig_uf, use_container_width=True)
            
        with c_chart2:
            st.subheader("🏙️ Principais Municípios")
            by_mun = df_ibge_ano.groupby(['Municipio', 'UF_Sigla'])['Producao_Kg'].sum().reset_index()
            by_mun['Local'] = by_mun['Municipio'] + " - " + by_mun['UF_Sigla']
            by_mun = by_mun.sort_values('Producao_Kg', ascending=False).head(10)
            
            fig_mun = px.bar(
                by_mun,
                x='Producao_Kg',
                y='Local',
                orientation='h',
                title=f"Top 10 Municípios em {sel_ano_ibge}",
                labels={'Producao_Kg': 'Produção (kg)', 'Local': ''}
            )
            fig_mun.update_layout(yaxis={'categoryorder': 'total ascending'}, separators=",.")
            st.plotly_chart(fig_mun, use_container_width=True)
            
        st.markdown("---")
        st.subheader("📈 Evolução da Produção Nacional")
        
        # Agrupar todo o historico por ano
        hist = df_ibge.groupby('Ano')['Producao_Kg'].sum().reset_index().sort_values('Ano')
        
        fig_hist = px.line(
            hist,
            x='Ano',
            y='Producao_Kg',
            markers=True,
            title="Série Histórica: Produção de Mel no Brasil",
            labels={'Producao_Kg': 'Produção (kg)'}
        )
        fig_hist.update_layout(separators=",.")
        st.plotly_chart(fig_hist, use_container_width=True)
        
        with st.expander("Ver Dados Brutos"):
            st.dataframe(df_ibge_ano.sort_values('Producao_Kg', ascending=False).style.format({
                'Producao_Kg': '{:,.0f}',
                'Valor_Prod_MilReais': '{:,.2f}'
            }), use_container_width=True)
            
    st.markdown("---")
    st.markdown(f"<div style='text-align: right; color: #666; font-size: 0.8em;'>Atualizado da fonte: IBGE / PPM em {get_db_updated_time()}</div>", unsafe_allow_html=True)


st.sidebar.caption("Desenvolvido por AntiGravity")
