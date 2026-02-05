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
    df = pd.read_sql("SELECT * FROM exportacoes_mel", conn)
    conn.close()
    return df

def format_br(val, is_currency=False):
    """Formata números para o padrão brasileiro."""
    if pd.isna(val): return ""
    if is_currency:
        return f"US$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{val:,.0f}".replace(",", ".")

try:
    df = load_data()
except Exception:
    st.error("Banco de dados não encontrado. Por favor, execute o processamento primeiro.")
    st.stop()

# Sidebar para filtros
st.sidebar.header("Filtros")
anos = sorted(df['Ano'].unique(), reverse=True)
selected_ano = st.sidebar.multiselect("Ano", anos, default=anos[:1])

df_filtered = df[df['Ano'].isin(selected_ano)]

# Filtro de UF
ufs = sorted(df_filtered['UF'].unique()) if 'UF' in df_filtered.columns else []
selected_uf = st.sidebar.multiselect("Estado (UF)", ufs)
if selected_uf:
    df_filtered = df_filtered[df_filtered['UF'].isin(selected_uf)]

# Filtro de Município
municipios = sorted(df_filtered['Municipio'].unique())
selected_mun = st.sidebar.multiselect("Município", municipios)
if selected_mun:
    df_filtered = df_filtered[df_filtered['Municipio'].isin(selected_mun)]

# Filtro de País
paises = sorted(df_filtered['Pais'].unique())
selected_pais = st.sidebar.multiselect("País", paises)
if selected_pais:
    df_filtered = df_filtered[df_filtered['Pais'].isin(selected_pais)]

# Título Principal
st.title("🍯 Radar de Exportação: Mel Natural (SH4 0409)")
st.markdown("---")

# KPIs Principais
col1, col2, col3 = st.columns(3)
total_usd = df_filtered['Valor_USD'].sum()
total_kg = df_filtered['Peso_KG'].sum()
avg_price = total_usd / total_kg if total_kg > 0 else 0

with col1:
    st.metric("Total Exportado (US$ FOB)", format_br(total_usd, True))
with col2:
    st.metric("Peso Líquido Total (KG)", f"{format_br(total_kg)} KG")
with col3:
    st.metric("Preço Médio (USD/KG)", format_br(avg_price, True))

st.markdown("---")

# Gráfico de Evolução (Linha)
st.subheader("📈 Evolução Temporal das Exportações (KG)")
if not df_filtered.empty:
    evolucao = df_filtered.groupby(['Ano', 'Mes', 'Mes_Num'])['Peso_KG'].sum().reset_index()
    evolucao = evolucao.sort_values(['Ano', 'Mes_Num'])

    fig_evolucao = px.line(evolucao, x='Mes', y='Peso_KG', color='Ano',
                           markers=True, labels={'Peso_KG': 'Peso (KG)', 'Mes': 'Mês'},
                           color_discrete_sequence=px.colors.qualitative.Safe)

    fig_evolucao.update_layout(separators=',.', hovermode="x unified")
    fig_evolucao.update_traces(hovertemplate='%{y:,.0f} KG')
    st.plotly_chart(fig_evolucao, use_container_width=True)
else:
    st.info("Nenhum dado disponível para o filtro selecionado.")

st.markdown("---")

# Gráficos de Barra
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
                              labels={'Valor_USD': 'Valor (US$)', 'Pais': 'País'},
                              custom_data=['Peso_KG', 'Preco_Medio'])
        
        fig_destinos.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, separators=',.')
        fig_destinos.update_traces(
            hovertemplate="<b>%{y}</b><br>Valor: US$ %{x:,.2f}<br>Peso: %{customdata[0]:,.0f} KG<br>Preço Médio: US$ %{customdata[1]:,.2f}"
        )
        st.plotly_chart(fig_destinos, use_container_width=True)
    else:
        st.info("Nenhum dado.")

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
                            labels={'Peso_KG': 'Peso (KG)', 'Municipio': 'Município'},
                            custom_data=['Valor_USD', 'Preco_Medio'])
        
        fig_muns.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, separators=',.')
        fig_muns.update_traces(
            hovertemplate="<b>%{y}</b><br>Peso: %{x:,.0f} KG<br>Valor: US$ %{customdata[0]:,.2f}<br>Preço Médio: US$ %{customdata[1]:,.2f}"
        )
        st.plotly_chart(fig_muns, use_container_width=True)
    else:
        st.info("Nenhum dado.")

# Tabela Detalhada
st.subheader("📋 Relatório Detalhado")

if not df_filtered.empty:
    # Preparar dataframe para exibição
    df_display = df_filtered.sort_values(['Ano', 'Mes_Num'], ascending=[False, False]).copy()
    
    # Ajuste para ordenação correta: adicionar prefixo numérico (ex: "01 - Janeiro")
    # Isso resolve o problema de ordenação alfabética mantendo a legibilidade
    df_display['Mes'] = df_display['Mes_Num'].astype(str).str.zfill(2) + ' - ' + df_display['Mes'].astype(str)
    
    # Adicionar coluna de Preço Médio
    df_display['Preco_Medio'] = df_display['Valor_USD'] / df_display['Peso_KG']
    
    # Selecionar e ordenar colunas finais
    colunas_finais = ['Ano', 'Mes', 'Municipio', 'UF', 'Pais', 'Valor_USD', 'Peso_KG', 'Preco_Medio']
    df_display = df_display[colunas_finais]

    # Botão de Download Excel
    output = io.BytesIO()
    # Convertemos para string antes de gerar o Excel para evitar erros com o tipo Categorical
    df_excel = df_display.copy()
    df_excel['Mes'] = df_excel['Mes'].astype(str)
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_excel.to_excel(writer, index=False, sheet_name='Exportacoes_Mel')
    
    st.download_button(
        label="📥 Baixar Tabela em Excel (.xlsx)",
        data=output.getvalue(),
        file_name=f"exportacoes_mel_detalhado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Exibição da Tabela com Filtros (st.dataframe já permite filtros de coluna em versões recentes)
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
st.caption("Dados extraídos automaticamente do MDIC Comex Stat (Dados Abertos).")
