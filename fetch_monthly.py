import comtradeapicall
import pandas as pd
import os
import time

# Configurações
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Chave de API
SUBSCRIPTION_KEY = "6383e7fcf14b4f48a842339b9a6fe4f6"

def fetch_monthly_data():
    print("Iniciando coleta de DADOS MENSAIS (Sazonalidade)...")
    
    # Para dados mensais, a API pode ser pesada.
    # Vamos focar nos principais fluxos: Exportações (Quem vendeu) e Importações totais.
    # period = YYYY ou YYYYMM. Podemos tentar pedir o ano todo de uma vez ou mês a mês.
    # A API v2 permite YYYY para retornar todos os meses se freqCode='M'.
    
    years = ['2023', '2024']
    flows = [
        {'code': 'X', 'name': 'Export', 'partner': '0'}, 
        {'code': 'M', 'name': 'Import', 'partner': '0'}
    ]
    
    # Gerar períodos mensais YYYYMM
    periods = []
    for year in years:
        for month in range(1, 13):
            primary_period = f"{year}{month:02d}"
            periods.append(primary_period)
            
    # Agrupar períodos em chunks de 6 meses para não estourar URL mas ser eficiente
    chunks = [periods[i:i + 6] for i in range(0, len(periods), 6)]
    periods_str_list = [",".join(chunk) for chunk in chunks]

    all_data = []

    for period_str in periods_str_list:
        for flow in flows:
            print(f"Solicitando {flow['name']} para meses: {period_str}...")
            try:
                df = comtradeapicall.getFinalData(
                    subscription_key=SUBSCRIPTION_KEY,
                    typeCode='C',
                    freqCode='M', 
                    clCode='HS',
                    period=period_str,
                    reporterCode=None, 
                    cmdCode='0409',
                    flowCode=flow['code'],
                    partnerCode=flow['partner'], 
                    partner2Code='0',
                    customsCode='C00',
                    motCode='0',
                    maxRecords=250000,
                    format_output='JSON'
                )
                
                if df is not None and not df.empty:
                    df['Tipo'] = flow['name']
                    print(f"  > {len(df)} registros encontrados.")
                    all_data.append(df)
                else:
                    print(f"  > Sem dados.")
                
                time.sleep(1) 
            
            except Exception as e:
                print(f"  > Erro: {e}")

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        target_path = os.path.join(DATA_DIR, "comtrade_monthly_raw.csv")
        final_df.to_csv(target_path, index=False)
        print(f"Sucesso! {len(final_df)} registros mensais salvos em {target_path}.")
    else:
        print("Nenhum dado mensal encontrado.")

if __name__ == "__main__":
    fetch_monthly_data()
