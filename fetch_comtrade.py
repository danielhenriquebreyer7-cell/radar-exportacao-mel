import requests
import pandas as pd
import os
import time

# Configurações
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# HS Code para Mel Natural (0409)
HS_CODE = "0409" 
# Período: No V2 o formato é YYYY
PERIOD = "2023,2024"

# API V2 Public Preview Endpoint
API_URL = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"

def fetch_global_honey_trade():
    print(f"Buscando dados globais de mel (HS {HS_CODE}) via API V2 (Public Preview)...")
    
    # Parâmetros para a API V2 Preview
    # Documentação não oficial sugere path structure, mas endpoint aceita query params também
    # Exemplo: /public/v1/preview/C/A/HS?reporterCode=...
    params = {
        'reporterCode': None, # All
        'period': PERIOD,
        'partnerCode': '0', # World
        'cmdCode': HS_CODE,
        'flowCode': 'X', # Exports
        'format': 'JSON'
    }

    try:
        response = requests.get(API_URL, params=params, timeout=60)
        
        if response.status_code != 200:
            print(f"Erro API: {response.status_code} - {response.text}")
            return False

        data = response.json()
        
        # O formato de resposta do Preview pode variar
        if 'data' in data and len(data['data']) > 0:
            df = pd.DataFrame(data['data'])
            target_path = os.path.join(DATA_DIR, "comtrade_global_honey_v2.csv")
            df.to_csv(target_path, index=False)
            print(f"Dados salvos em: {target_path}")
            print(f"Sucesso! {len(df)} registros baixados.")
            return True
        else:
            print(f"Nenhum dado encontrado ou resposta vazia: {data}")
            return False
            
    except Exception as e:
        print(f"Erro ao acessar API Comtrade V2: {e}")
        return False

if __name__ == "__main__":
    fetch_global_honey_trade()
