import comtradeapicall
import pandas as pd
import os
import time

# Configurações
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Chave de API
SUBSCRIPTION_KEY = "6383e7fcf14b4f48a842339b9a6fe4f6"

def fetch_bilateral_data():
    print("Iniciando coleta de DADOS BILATERAIS (Quem vende pra quem)...")
    
    # Vamos focar em 2023 primeiro para testar o volume
    years = ['2023', '2024'] 
    all_data = []

    for year in years:
        print(f"Solicitando Bilateral (X) para {year}...")
        try:
            # Para economizar e evitar timeout, vamos focar nos Top Exportadores?
            # Ou tentar pegar tudo de uma vez?
            # Tentar pegar tudo: reporter=None, partner=None
            
            df = comtradeapicall.getFinalData(
                subscription_key=SUBSCRIPTION_KEY,
                typeCode='C',
                freqCode='A',
                clCode='HS',
                period=year,
                reporterCode=None, # All Reporters
                cmdCode='0409',
                flowCode='X', # Exports
                partnerCode=None, # All Partners (Isso deve retornar a quebra por país destino)
                partner2Code='0',
                customsCode='C00',
                motCode='0',
                maxRecords=250000,
                format_output='JSON'
            )
            
            if df is not None and not df.empty:
                # Filtrar para remover o agregado global ("World") que já temos
                # Geralmente partnerCode 0 é World. Queremos o detalhe.
                df_bilateral = df[df['partnerCode'] != 0]
                print(f"  > {len(df)} registros totais. {len(df_bilateral)} bilaterais úteis para {year}.")
                all_data.append(df_bilateral)
            else:
                print(f"  > Nenhum dado para {year}.")
            
            time.sleep(2)
            
        except Exception as e:
            print(f"  > Erro ao buscar {year}: {e}")

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        target_path = os.path.join(DATA_DIR, "comtrade_bilateral_raw.csv")
        final_df.to_csv(target_path, index=False)
        print(f"Sucesso! {len(final_df)} registros bilaterais salvos em {target_path}.")
        return True
    else:
        print("Nenhum dado bilateral encontrado.")
        return False

if __name__ == "__main__":
    fetch_bilateral_data()
