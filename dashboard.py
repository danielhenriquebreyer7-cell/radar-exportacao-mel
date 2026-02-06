import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import io

# Configuração da página para um visual premium
st.set_page_config(page_title="Radar de Exportação: Mel Natural", layout="wide")

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
        
    try:
        df_fao_prod = pd.read_sql("SELECT * FROM fao_production", conn)
    except Exception:
        df_fao_prod = pd.DataFrame()

    try:
        df_fao_price = pd.read_sql("SELECT * FROM fao_prices", conn)
    except Exception:
        df_fao_price = pd.DataFrame()

    conn.close()
    return df_br, df_global, df_bilateral, df_mensal, df_fao_prod, df_fao_price

def format_br(val, is_currency=False):
    """Formata números para o padrão brasileiro."""
    if pd.isna(val): return ""
    if is_currency:
        return f"US$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{val:,.0f}".replace(",", ".")

try:
    df, df_global, df_bilateral, df_mensal, df_fao_prod, df_fao_price = load_data()
except Exception:
    st.error("Banco de dados não encontrado. Por favor, execute o processamento primeiro.")
    st.stop()
    


# Navegação Lateral
st.sidebar.title("Navegação")
view_mode = st.sidebar.radio("Selecione a Visão:", 
    ["Visão Brasil (Local)", "Visão Global (Mundo)", "Inteligência de Produção (FAO)"]
)

if view_mode == "Visão Brasil (Local)":
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
    
    st.subheader("📈 Evolução Temporal (KG)")
    if not df_filtered.empty:
        evolucao = df_filtered.groupby(['Ano', 'Mes', 'Mes_Num'])['Peso_KG'].sum().reset_index()
        evolucao = evolucao.sort_values(['Ano', 'Mes_Num'])
        fig_evolucao = px.line(evolucao, x='Mes', y='Peso_KG', color='Ano', markers=True)
        fig_evolucao.update_layout(separators=",.")
        st.plotly_chart(fig_evolucao, use_container_width=True)
    
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.subheader("Destinos Principais")
        if not df_filtered.empty:
            destinos = df_filtered.groupby('Pais')['Valor_USD'].sum().reset_index().sort_values('Valor_USD', ascending=False).head(10)
            fig_destinos = px.bar(destinos, x='Valor_USD', y='Pais', orientation='h', color='Valor_USD')
            fig_destinos.update_layout(yaxis={'categoryorder':'total ascending'}, separators=",.")
            st.plotly_chart(fig_destinos, use_container_width=True)
            
    with row1_col2:
        st.subheader("Municípios Exportadores")
        if not df_filtered.empty:
            muns = df_filtered.groupby('Municipio')['Peso_KG'].sum().reset_index().sort_values('Peso_KG', ascending=False).head(10)
            fig_muns = px.bar(muns, x='Peso_KG', y='Municipio', orientation='h', color='Peso_KG')
            fig_muns.update_layout(yaxis={'categoryorder':'total ascending'}, separators=",.")
            st.plotly_chart(fig_muns, use_container_width=True)

    # ... (Tabela Detalhada Brasil - Omitindo detalhes para brevidade, mas mantendo funcionalidade se necessário) ...
    
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

elif view_mode == "Inteligência de Produção (FAO)":
    st.title("🚜 Inteligência de Produção (FAOSTAT)")
    st.markdown("**Fonte:** FAO (QCL & Prices) | **Foco:** Produção Mundial e Preços ao Produtor")
    st.markdown("---")

    if df_fao_prod.empty:
        st.warning("Dados FAO não carregados / tabela vazia. Execute o processamento.")
    else:
        # Sidebar Filters FAO
        st.sidebar.header("Filtros FAO")
        # Filtrar anos > 0
        anos_fao = sorted(df_fao_prod[df_fao_prod['Ano'] > 0]['Ano'].unique(), reverse=True)
        if not anos_fao:
             st.error("Sem dados de anos válidos.")
             st.stop()
             
        sel_ano_fao = st.sidebar.selectbox("Selecione o Ano Base", anos_fao)

        prod_ano = df_fao_prod[df_fao_prod['Ano'] == sel_ano_fao]
        price_ano = df_fao_price[df_fao_price['Ano'] == sel_ano_fao] if not df_fao_price.empty else pd.DataFrame()

        # KPIs
        total_prod = prod_ano['Producao_Ton'].sum()
        total_colmeias = prod_ano['Colmeias'].sum()
        
        # Calcular produtividade global ponderada?? Ou média simples dos países?
        # Média simples dos países pode ser enganosa. Vamos usar Global Yield = Total Prod / Total Colmeias
        avg_yield_global = (total_prod * 1000) / total_colmeias if total_colmeias > 0 else 0

        # Maior produtor
        max_producer = "-"
        if not prod_ano.empty:
            max_prod_row = prod_ano.loc[prod_ano['Producao_Ton'].idxmax()]
            max_producer = f"{max_prod_row['Pais']}"

        # Layout Métricas
        c1, c2, c3, c4 = st.columns(4)
        fmt_br = lambda x: f"{x:,.0f}".replace(",", ".")
        fmt_br_dec = lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        c1.metric(f"Produção ({sel_ano_fao})", f"{fmt_br(total_prod)} Ton")
        c2.metric("Colmeias (Estoque)", f"{fmt_br(total_colmeias)}")
        c3.metric("Produtividade Média", f"{fmt_br_dec(avg_yield_global)} kg/colmeia")
        
        avg_price_global = 0
        if not price_ano.empty:
             avg_price_global = price_ano['Price_USD'].mean()
        
        c4.metric("Preço Médio (USD)", f"$ {fmt_br_dec(avg_price_global)}")

        st.markdown("---")

        # Chart 1: Top Producers
        c_chart1, c_chart2 = st.columns(2)
        
        with c_chart1:
            st.subheader(f"🏆 Top 15 Produtores (Ton)")
            top_prod = prod_ano.sort_values('Producao_Ton', ascending=False).head(15)
            top_prod['Color'] = top_prod['Pais'].apply(lambda x: '#009c3b' if 'Brazil' in str(x) else '#1f77b4')
            
            fig_prod = px.bar(top_prod, x='Producao_Ton', y='Pais', orientation='h', 
                              text_auto='.2s', color='Color', color_discrete_map='identity')
            fig_prod.update_layout(yaxis={'categoryorder':'total ascending'}, separators=",.", showlegend=False)
            st.plotly_chart(fig_prod, use_container_width=True)

        with c_chart2:
            st.subheader(f"🐝 Top 10 Produtividade (kg/colmeia)")
            # Filtrar quem tem produção e colmeias mínimas para evitar outliers de micro-estados
            df_yield = prod_ano[(prod_ano['Producao_Ton'] > 500) & (prod_ano['Colmeias'] > 1000)].copy()
            top_yield = df_yield.sort_values('Yield_Kg_Colmeia', ascending=False).head(10)
            
            fig_yield = px.bar(top_yield, x='Yield_Kg_Colmeia', y='Pais', orientation='h',
                               text_auto='.1f', color_discrete_sequence=['#ff7f0e'])
            fig_yield.update_layout(yaxis={'categoryorder':'total ascending'}, separators=",.", xaxis_title="kg por colmeia")
            st.plotly_chart(fig_yield, use_container_width=True)

        # Chart 2: Price vs Prod
        if not price_ano.empty:
            st.markdown("---")
            st.subheader(f"💰 Eficiência: Volume vs Preço ({sel_ano_fao})")
            st.caption("Tamanho da bolha = Quantidade de Colmeias | Cor = Produtividade")
            
            df_merged = pd.merge(prod_ano, price_ano, on=['Pais', 'Ano'], how='inner')
            
            if not df_merged.empty:
                df_merged = df_merged[df_merged['Price_USD'] > 0]
                
                fig_scatter = px.scatter(
                    df_merged, 
                    x='Producao_Ton', 
                    y='Price_USD', 
                    size='Colmeias', 
                    color='Yield_Kg_Colmeia',
                    hover_name='Pais',
                    hover_data=['Producao_Ton', 'Price_USD', 'Colmeias'],
                    labels={
                        'Producao_Ton': 'Produção (Ton)', 
                        'Price_USD': 'Preço Produtor (USD)',
                        'Colmeias': 'Nº Colmeias',
                        'Yield_Kg_Colmeia': 'Yield (kg/col)'
                    },
                    log_x=True,
                    color_continuous_scale='Viridis'
                )
                fig_scatter.update_layout(separators=",.")
                st.plotly_chart(fig_scatter, use_container_width=True)
                
                with st.expander("Ver Tabela Detalhada (FAO)"):
                    st.dataframe(df_merged[['Pais', 'Producao_Ton', 'Colmeias', 'Yield_Kg_Colmeia', 'Price_USD']].sort_values('Producao_Ton', ascending=False).style.format({
                        'Producao_Ton': "{:,.0f}",
                        'Colmeias': "{:,.0f}",
                        'Yield_Kg_Colmeia': "{:,.1f}",
                        'Price_USD': "${:,.2f}"
                    }))
            else:
                 st.info("Sem dados de preço cruzados para este ano.")

st.sidebar.markdown("---")
st.sidebar.caption("Desenvolvido por AntiGravity")
