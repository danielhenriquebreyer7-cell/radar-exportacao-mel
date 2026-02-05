import requests
import pandas as pd
import os

def fetch_ibge_metadata():
    print("Buscando dados de municípios do IBGE...")
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        mun_list = []
        for item in data:
            try:
                # Código IBGE de 7 dígitos
                # A estrutura é item['id'], item['nome'], item['municipio']['microrregiao']... 
                # Dependendo do endpoint, vamos validar o item.
                mun_list.append({
                    'CO_MUN': str(item['id']),
                    'NO_MUN': item['nome'],
                    'SG_UF': item['microrregiao']['mesorregiao']['UF']['sigla']
                })
            except Exception:
                continue
        
        df_mun = pd.DataFrame(mun_list)
        os.makedirs("metadata", exist_ok=True)
        df_mun.to_csv("metadata/MUNICIPIO_IBGE.csv", index=False, sep=';', encoding='utf-8')
        print(f"Sucesso! {len(df_mun)} municípios salvos.")
    except Exception as e:
        print(f"Erro ao buscar dados do IBGE: {e}")

if __name__ == "__main__":
    fetch_ibge_metadata()
