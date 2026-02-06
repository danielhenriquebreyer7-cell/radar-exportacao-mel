import pandas as pd
import os

# Configurações
EXPORT_DIR = "analise_exploratoria"
os.makedirs(EXPORT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(EXPORT_DIR, "dicionario_de_dados.xlsx")

# Dados de Negócio
dados_negocio = [
    {"Coluna": "refYear", "Significado": "Ano de referência", "Observação": "É o ano oficial do dado (Ex: 2023, 2024)."},
    {"Coluna": "reporterDesc", "Significado": "Quem reportou", "Observação": "O país que está declarando a transação (Ex: Brazil, China)."},
    {"Coluna": "flowDesc", "Significado": "Tipo de Movimento", "Observação": "Export: Venda (País vendeu). Import: Compra (País comprou)."},
    {"Coluna": "partnerDesc", "Significado": "Parceiro Comercial", "Observação": "Com quem foi a troca. Como buscamos partnerCode=0, aqui sempre será World (Mundo)."},
    {"Coluna": "cmdCode / cmdDesc", "Significado": "Produto", "Observação": "0409 / Natural Honey."},
    {"Coluna": "primaryValue", "Significado": "Valor Financeiro", "Observação": "Valor total da transação em USD (Dólares)."},
    {"Coluna": "netWgt", "Significado": "Peso Líquido", "Observação": "Volume em KG (Quilogramas). Use para calcular preço médio."},
    {"Coluna": "fobvalue", "Significado": "Valor FOB", "Observação": "Free On Board. Geralmente igual ao primaryValue nas exportações."},
    {"Coluna": "cifvalue", "Significado": "Valor CIF", "Observação": "Cost, Insurance and Freight. Inclui frete/seguro (usado em Importações)."}
]

# Metadados
metadados = [
    {"Coluna": "reporterCode", "Significado": "Código do País", "Observação": "76 = Brasil. Útil para joins com outras tabelas."},
    {"Coluna": "period", "Significado": "Período Técnico", "Observação": "20230101 (formato interno para 2023 anual)."},
    {"Coluna": "freqCode", "Significado": "Frequência", "Observação": "A = Anual (Annual)."},
    {"Coluna": "customsCode", "Significado": "Regime Aduaneiro", "Observação": "C00 = Comércio Geral."},
    {"Coluna": "motDesc", "Significado": "Meio de Transporte", "Observação": "Mostra se foi Avião, Navio, etc. (Geralmente vazio em dados anuais)."},
    {"Coluna": "qty / altQty", "Significado": "Quantidades Alt.", "Observação": "Unidades alternativas. Massas e pesos (netWgt) são mais confiáveis para Mel."},
    {"Coluna": "isQtyEstimated", "Significado": "Dado Estimado?", "Observação": "True/False. Avisa se o valor foi calculado ou reportado real."},
    {"Coluna": "isAggregate", "Significado": "Agregado?", "Observação": "True. Confirma que é uma soma total."}
]

def create_dictionary():
    print(f"Gerando dicionário em {OUTPUT_FILE}...")
    try:
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
            pd.DataFrame(dados_negocio).to_excel(writer, index=False, sheet_name="Dados de Negócio")
            pd.DataFrame(metadados).to_excel(writer, index=False, sheet_name="Metadados Técnicos")
        print("Sucesso!")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    create_dictionary()
