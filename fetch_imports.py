import comtradeapicall
import pandas as pd
import os
import time

# Configurações
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Chave de API
SUBSCRIPTION_KEY = "6383e7fcf14b4f48a842339b9a6fe4f6"

def fetch_import_data():
    print("Iniciando coleta de IMPORTAÇÕES globais (UN Comtrade)...")
    
    # Lista de anos
    years = ['2023', '2024'] 
    all_data = []

    for year in years:
        print(f"Solicitando Importações (M) para {year}...")
        try:
            df = comtradeapicall.getFinalData(
                subscription_key=SUBSCRIPTION_KEY,
                typeCode='C',
                freqCode='A',
                clCode='HS',
                period=year,
                reporterCode=None,
                cmdCode='0409',
                flowCode='M', # M = Import
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
            
            time.sleep(2)
            
        except Exception as e:
            print(f"  > Erro ao buscar {year}: {e}")

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        target_path = os.path.join(DATA_DIR, "comtrade_global_honey_imports.csv")
        final_df.to_csv(target_path, index=False)
        print(f"Sucesso! {len(final_df)} registros de importação salvos em {target_path}.")
        return True
    else:
        print("Nenhuma importação encontrada.")
        return False

if __name__ == "__main__":
    fetch_import_data()
