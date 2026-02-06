"""
FAO Data Fetcher - v2 (Reconstruído)
Baixa dados de Produção, Colmeias e Preços ao Produtor para Mel Natural.
"""
import requests
import pandas as pd
import os
import zipfile
import io

# Configurações
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# URLs FAO Bulk (Formato Normalizado)
URL_PRODUCTION = "https://fenixservices.fao.org/faostat/static/bulkdownloads/Production_Crops_Livestock_E_All_Data_(Normalized).zip"
URL_PRICES = "https://fenixservices.fao.org/faostat/static/bulkdownloads/Prices_E_All_Data_(Normalized).zip"

# Códigos FAO
ITEM_HONEY = 1182        # Natural honey
ITEM_BEEHIVES = 1181     # Bees (Beehives)
ELEM_PRODUCTION = 5510   # Production (tonnes)
ELEM_STOCKS = 5114       # Stocks (number of beehives)
ELEM_PRICE_USD = 5532    # Producer Price (USD/tonne)


def download_zip(url: str, cache_name: str) -> str | None:
    """Baixa arquivo ZIP e salva em cache local."""
    cache_path = os.path.join(DATA_DIR, cache_name)
    
    if os.path.exists(cache_path):
        print(f"  [CACHE] {cache_name} já existe.")
        return cache_path
    
    print(f"  [DOWNLOAD] Baixando {cache_name}...")
    try:
        r = requests.get(url, stream=True, timeout=120)
        r.raise_for_status()
        with open(cache_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  [OK] {cache_name} salvo.")
        return cache_path
    except Exception as e:
        print(f"  [ERRO] Falha ao baixar {cache_name}: {e}")
        return None


def extract_and_filter(zip_path: str, filters: list[dict]) -> pd.DataFrame:
    """
    Extrai CSV do ZIP e filtra por Item Code + Element Code.
    filters: lista de dicts com 'item' e 'element' keys
    """
    print(f"  [EXTRACT] Processando {zip_path}...")
    
    with zipfile.ZipFile(zip_path) as z:
        csv_name = [n for n in z.namelist() if n.endswith('.csv')][0]
        
        chunks = []
        with z.open(csv_name) as f:
            for chunk in pd.read_csv(f, encoding='latin-1', chunksize=50000):
                # Aplicar filtros
                mask = pd.Series([False] * len(chunk))
                for filt in filters:
                    m = (chunk['Item Code'] == filt['item']) & (chunk['Element Code'] == filt['element'])
                    mask = mask | m
                
                filtered = chunk[mask]
                if not filtered.empty:
                    chunks.append(filtered)
    
    if chunks:
        df = pd.concat(chunks, ignore_index=True)
        print(f"  [OK] {len(df)} registros encontrados.")
        return df
    else:
        print("  [AVISO] Nenhum dado encontrado.")
        return pd.DataFrame()


def main():
    print("=" * 50)
    print("FAO Data Fetcher v2")
    print("=" * 50)
    
    # 1. Produção + Colmeias
    print("\n[1/2] Produção e Colmeias:")
    zip_prod = download_zip(URL_PRODUCTION, "fao_qcl_bulk.zip")
    
    if zip_prod:
        df_prod = extract_and_filter(zip_prod, [
            {'item': ITEM_HONEY, 'element': ELEM_PRODUCTION},
            {'item': ITEM_BEEHIVES, 'element': ELEM_STOCKS}
        ])
        
        if not df_prod.empty:
            # Salvar CSV limpo
            output_path = os.path.join(DATA_DIR, "fao_production_raw.csv")
            df_prod.to_csv(output_path, index=False)
            print(f"  [SALVO] {output_path}")
    
    # 2. Preços
    print("\n[2/2] Preços ao Produtor:")
    zip_prices = download_zip(URL_PRICES, "fao_prices_bulk.zip")
    
    if zip_prices:
        df_prices = extract_and_filter(zip_prices, [
            {'item': ITEM_HONEY, 'element': ELEM_PRICE_USD}
        ])
        
        if not df_prices.empty:
            output_path = os.path.join(DATA_DIR, "fao_prices_raw.csv")
            df_prices.to_csv(output_path, index=False)
            print(f"  [SALVO] {output_path}")
    
    print("\n" + "=" * 50)
    print("Coleta FAO concluída!")
    print("=" * 50)


if __name__ == "__main__":
    main()
