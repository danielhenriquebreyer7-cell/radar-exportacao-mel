import requests
import pandas as pd
import os
import zipfile
import io

# Configurações
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# FAO Bulk URLs (Normalized = Long Format)
URL_PROD = "https://fenixservices.fao.org/faostat/static/bulkdownloads/Production_Crops_Livestock_E_All_Data_(Normalized).zip"
URL_PRICES = "https://fenixservices.fao.org/faostat/static/bulkdownloads/Prices_E_All_Data_(Normalized).zip"

# Filtros (Podem precisar de ajuste)
ITEM_CODE_HONEY = 1182 # Natural honey (Confirmed via debug)
ELEMENT_PROD = 5510          # Production (tonnes)
ELEMENT_PRICE_LCU = 5530     # Producer Price (LCU/tonne)
ELEMENT_PRICE_USD = 5532     # Producer Price (USD/tonne)

def download_file(url, filename):
    local_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(local_path):
        print(f"Arquivo {filename} já existe. Usando cache.")
        return local_path
        
    print(f"Baixando {filename} (pode demorar)...")
    try:
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Download concluído: {local_path}")
        return local_path
    except Exception as e:
        print(f"Erro ao baixar {filename}: {e}")
        return None

def process_zip(zip_path, name, item_code, elements, debug=False):
    print(f"[{name}] Processando {zip_path}...")
    try:
        z = zipfile.ZipFile(zip_path)
        csv_filename = [n for n in z.namelist() if n.endswith('.csv')][0]
        print(f"[{name}] Lendo CSV: {csv_filename}")
        
        chunks = []
        found_honey = False
        
        with z.open(csv_filename) as f:
            # Ler primeiro chunk para debug
            first_chunk = True
            
            for chunk in pd.read_csv(f, encoding='latin-1', chunksize=50000):
                if first_chunk and debug:
                    print(f"[{name}] Colunas encontradas: {list(chunk.columns)}")
                    # Procurar MEL
                    honey_rows = chunk[chunk['Item'].astype(str).str.contains('Honey', case=False, na=False)]
                    if not honey_rows.empty:
                        print(f"[{name}] Exemplo de dados de Mel encontrados:")
                        print(honey_rows[['Item Code', 'Item']].drop_duplicates().head())
                    else:
                        print(f"[{name}] AVISO: 'Honey' não encontrado no primeiro chunk (pode estar mais adiante).")
                    first_chunk = False

                # Filtrar
                # Normalizar nomes de colunas (as vezes vem com Code ou sem)
                # Vamos verificar se 'Item Code' existe
                target_df = chunk.copy()
                
                # Definir máscaras de interesse com base no tipo de arquivo
                if name == "production":
                    # 1. Mel (1182) -> Produção (5510)
                    mask_honey = (target_df['Item Code'] == 1182) & (target_df['Element Code'] == 5510)
                    # 2. Colmeias (1181) -> Stocks (5111)
                    mask_hives = (target_df['Item Code'] == 1181) & (target_df['Element Code'] == 5111)
                    mask = mask_honey | mask_hives
                else:
                    # Preços (Item 1182, Elementos passados)
                    mask = (target_df['Item Code'] == item_code) & (target_df['Element Code'].isin(elements))
                
                filtered = target_df[mask]
                
                if not filtered.empty:
                    chunks.append(filtered)
                    if not found_honey:
                         # Debug info
                         print(f"[{name}] DADOS ENCONTRADOS! Amostra:")
                         print(filtered[['Item', 'Element', 'Year', 'Value']].head(2))
                         found_honey = True
        
        if chunks:
            df_final = pd.concat(chunks, ignore_index=True)
            output_path = os.path.join(DATA_DIR, f"fao_{name}_honey.csv")
            df_final.to_csv(output_path, index=False)
            print(f"[{name}] Sucesso! {len(df_final)} registros salvos em {output_path}")
        else:
            print(f"[{name}] Aviso: Nenhum dado encontrado para o Item {item_code}")

    except Exception as e:
        print(f"[{name}] Erro: {e}")

def main():
    print("=== Coleta FAO (Cache + Debug) ===")
    
    # 1. Produção
    zip_prod = download_file(URL_PROD, "fao_production_raw.zip")
    if zip_prod:
         process_zip(zip_prod, "production", ITEM_CODE_HONEY, [ELEMENT_PROD], debug=True)
    
    # 2. Preços
    zip_prices = download_file(URL_PRICES, "fao_prices_raw.zip")
    if zip_prices:
         process_zip(zip_prices, "prices", ITEM_CODE_HONEY, [ELEMENT_PRICE_LCU, ELEMENT_PRICE_USD], debug=True)

if __name__ == "__main__":
    main()
