import comtradeapicall
import pandas as pd
import os
import time

# Configurações
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Chave de API fornecida pelo usuário
SUBSCRIPTION_KEY = "6383e7fcf14b4f48a842339b9a6fe4f6"

def fetch_comtrade_data():
    print("Iniciando coleta de dados globais da UN Comtrade (V2 - Key Authenticated)...")
    
    # Lista de anos para buscar individualmente (limite da API)
    years = ['2023', '2024'] 
    all_data = []

    for year in years:
        print(f"Solicitando dados para {year}...")
        try:
            df = comtradeapicall.getFinalData(
                subscription_key=SUBSCRIPTION_KEY,
                typeCode='C',
                freqCode='A',
                clCode='HS',
                period=year,
                reporterCode=None,
                cmdCode='0409',
                flowCode='X',
                partnerCode='0',
                partner2Code='0',
                customsCode='C00',
                motCode='0',
                maxRecords=250000,
                format_output='JSON'
            )
            
            if df is not None and not df.empty:
                print(f"  > {len(df)} registros encontrados para {year}.")
                all_data.append(df)
            else:
                print(f"  > Nenhum dado para {year}.")
            
            # Respeitar rate limit
            time.sleep(2)
            
        except Exception as e:
            print(f"  > Erro ao buscar {year}: {e}")

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        print(f"\nTotal consolidado: {len(final_df)} registros.")
        
        # Salvar dados brutos
        target_path = os.path.join(DATA_DIR, "comtrade_global_honey_full.csv")
        final_df.to_csv(target_path, index=False)
        print(f"Dados salvos em: {target_path}")
        
        # Exibir colunas e primeiras linhas para ajudar no processor
        print("\nColunas do dataset:")
        print(final_df.columns.tolist())
        
        print("\nExemplo dos dados:")
        cols_to_show = ['period', 'reporterDesc', 'cmdCode', 'primaryValue', 'netWgt']
        print(final_df[[c for c in cols_to_show if c in final_df.columns]].head())
        return True
    else:
        print("Nenhum dado foi coletado.")
        return False

if __name__ == "__main__":
    fetch_comtrade_data()
