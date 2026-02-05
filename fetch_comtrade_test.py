import requests
import pandas as pd
import os

# Configurações
DATA_DIR = "data"
# HS Code para Mel Natural (0409)
HS_CODE = "0409" 
# Período: No V2 o formato é YYYY
PERIOD = "2023,2024"

# API V2 Public Endpoint (Preview)
# Não exige chave para consultas pequenas
API_URL = "https://comtradeapi.un.org/public/v1/getFinalData"

def fetch_global_honey_trade():
    print(f"Buscando dados globais de mel (HS {HS_CODE}) via API V2 (Public)...")
    
    # Parâmetros para a API V2
    # typeCode=C (Commodities), freqCode=A (Annual), clCode=HS (Harmonized System)
    # flowCode=X (Exports)
    params = {
        'typeCode': 'C',
        'freqCode': 'A',
        'clCode': 'HS',
        'period': PERIOD,
        'reporterCode': None, # All reporters
        'cmdCode': HS_CODE,
        'flowCode': 'X', 
        'format': 'JSON'
    }

    try:
        response = requests.get(API_URL, params=params, timeout=60)
        # Se a resposta for 200 mas vazia, o V2 às vezes retorna erro no JSON
        response.raise_for_status()
        
        data = response.json()
        if 'data' in data and len(data['data']) > 0:
            df = pd.DataFrame(data['data'])
            os.makedirs(DATA_DIR, exist_ok=True)
            target_path = os.path.join(DATA_DIR, "comtrade_global_honey_v2.csv")
            df.to_csv(target_path, index=False)
            print(f"Dados salvos em: {target_path}")
            print(f"Sucesso! {len(df)} registros baixados.")
            return True
        else:
            print(f"Nenhum dado encontrado ou limite de taxa atingido: {data}")
            return False
    except Exception as e:
        print(f"Erro ao acessar API Comtrade V2: {e}")
        return False

if __name__ == "__main__":
    fetch_global_honey_trade()
