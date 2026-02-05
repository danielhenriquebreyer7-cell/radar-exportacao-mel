import requests
import pandas as pd
import os
import time

# Configurações
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# HS Code para Mel Natural (0409)
HS_CODE = "0409" 
# Lista de Anos
YEARS = ["2022", "2023", "2024"]

# API V2 Public Preview Endpoint
# Documentado via engenharia reversa de casos de uso comuns
API_URL = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"

def fetch_global_honey_trade():
    print(f"Buscando dados globais de mel (HS {HS_CODE}) via API V2 (Public Preview)...")
    
    all_data = []

    for year in YEARS:
        print(f"  > Solicitando ano {year}...")
        params = {
            'reporterCode': None, # All
            'period': year,
            'partnerCode': '0', # World
            'cmdCode': HS_CODE,
            'flowCode': 'X', # Exports
            'format': 'JSON'
        }

        try:
            response = requests.get(API_URL, params=params, timeout=60)
            
            if response.status_code != 200:
                print(f"    Erro API: {response.status_code} - {response.text}")
                continue

            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                count = len(data['data'])
                print(f"    {count} registros encontrados.")
                all_data.extend(data['data'])
            else:
                print(f"    Nenhum dado encontrado para {year}.")
            
            # Pausa para evitar rate limit
            time.sleep(2)
            
        except Exception as e:
            print(f"    Erro ao acessar API Comtrade V2: {e}")

    if all_data:
        df = pd.DataFrame(all_data)
        target_path = os.path.join(DATA_DIR, "comtrade_global_honey_v2.csv")
        df.to_csv(target_path, index=False)
        print(f"Sucesso! Total de {len(df)} registros baixados e salvos em {target_path}.")
        return True
    else:
        print("Falha: Nenhum dado coletado de nenhum ano.")
        return False

if __name__ == "__main__":
    fetch_global_honey_trade()
