"""
FAO Data Fetcher - v4 (Bulk Download com Headers de Navegador)
Utiliza bulk download com headers adequados para evitar bloqueio 403.
Baseado na documentação oficial da FAOSTAT.
"""
import requests
import pandas as pd
import os
import zipfile
import io

# Configurações
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Headers para simular navegador (evita bloqueio 403)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,pt-BR;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.fao.org/faostat/en/',
}

# URLs FAO Bulk (fenixservices.fao.org)
# Dataset correto para Mel: QCL (Crops and Livestock Products)
URL_PRODUCTION = "https://fenixservices.fao.org/faostat/static/bulkdownloads/Production_Crops_Livestock_E_All_Data_(Normalized).zip"
URL_PRICES = "https://fenixservices.fao.org/faostat/static/bulkdownloads/Prices_E_All_Data_(Normalized).zip"

# URLs alternativas (servidores bulks-faostat)
URL_PRODUCTION_ALT = "https://bulks-faostat.fao.org/production/Production_LivestockPrimary_E_All_Data_(Normalized).zip"
URL_PRICES_ALT = "https://bulks-faostat.fao.org/production/Prices_E_All_Data_(Normalized).zip"

# Códigos FAO
ITEM_HONEY = 1182  # Natural honey

# Mapeamento de elementos
ELEM_PRODUCTION_CODES = [5510, 5513, 2510]           # Production quantity (tonnes)
ELEM_BEEHIVES_CODES = [5111, 5114, 5320, 5321, 2313] # Stocks/Producing animals
ELEM_PRICE_CODES = [5532, 5530]                       # Producer Price USD


def download_zip(url: str, cache_name: str, use_alt: bool = False) -> str | None:
    """Baixa arquivo ZIP com headers de navegador e salva em cache local."""
    cache_path = os.path.join(DATA_DIR, cache_name)
    
    # Verificar cache existente (se maior que 1MB, assumir válido)
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1024 * 1024:
        size_mb = os.path.getsize(cache_path) // (1024 * 1024)
        print(f"  [CACHE] {cache_name} já existe ({size_mb} MB). Usando cache.")
        return cache_path
    
    print(f"  [DOWNLOAD] Baixando de: {url}")
    
    try:
        # Usar sessão para manter cookies
        session = requests.Session()
        session.headers.update(HEADERS)
        
        # Primeira requisição para obter cookies
        response = session.get(url, stream=True, timeout=300, allow_redirects=True)
        
        if response.status_code == 403:
            print(f"  [AVISO] 403 Forbidden. Status: Acesso negado.")
            return None
        
        response.raise_for_status()
        
        # Salvar arquivo
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(cache_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = (downloaded / total_size) * 100
                        print(f"\r  Progresso: {pct:.1f}%", end='', flush=True)
        
        print()  # Nova linha após progresso
        
        final_size = os.path.getsize(cache_path)
        if final_size > 1024 * 1024:
            print(f"  [OK] {cache_name} salvo ({final_size // (1024*1024)} MB).")
            return cache_path
        else:
            print(f"  [AVISO] Arquivo muito pequeno ({final_size} bytes), pode estar corrompido.")
            os.remove(cache_path)
            return None
            
    except requests.exceptions.HTTPError as e:
        print(f"  [ERRO HTTP] {e}")
        return None
    except requests.exceptions.Timeout:
        print("  [ERRO] Timeout na requisição (300s)")
        return None
    except Exception as e:
        print(f"  [ERRO] {e}")
        return None


def extract_and_filter(zip_path: str, item_codes: list, element_codes: list) -> pd.DataFrame:
    """Extrai e filtra o CSV do bulk mantendo apenas o necessário."""
    print(f"  [EXTRACT] Processando {os.path.basename(zip_path)}...")
    
    try:
        with zipfile.ZipFile(zip_path) as z:
            # Encontrar CSV normalizado
            csv_names = [n for n in z.namelist() if n.endswith('.csv') and 'Normalized' in n]
            
            if not csv_names:
                print("  [ERRO] Nenhum CSV normalizado encontrado no ZIP")
                return pd.DataFrame()
            
            csv_name = csv_names[0]
            print(f"  Extraindo {csv_name}...")
            
            chunks = []
            with z.open(csv_name) as f:
                # Ler em blocos para não estourar RAM
                for chunk in pd.read_csv(f, encoding='latin-1', chunksize=100000):
                    # Verificar nomes de colunas
                    item_col = 'Item Code' if 'Item Code' in chunk.columns else 'ItemCode'
                    elem_col = 'Element Code' if 'Element Code' in chunk.columns else 'ElementCode'
                    
                    if item_col not in chunk.columns or elem_col not in chunk.columns:
                        continue
                    
                    mask = (chunk[item_col].isin(item_codes)) & (chunk[elem_col].isin(element_codes))
                    filtered = chunk[mask]
                    if not filtered.empty:
                        chunks.append(filtered)
        
        if chunks:
            df = pd.concat(chunks, ignore_index=True)
            print(f"  [OK] {len(df)} registros encontrados.")
            return df
        else:
            print("  [AVISO] Nenhum dado encontrado para os filtros especificados.")
            return pd.DataFrame()
            
    except zipfile.BadZipFile:
        print("  [ERRO] Arquivo ZIP corrompido")
        return pd.DataFrame()
    except Exception as e:
        print(f"  [ERRO] {e}")
        return pd.DataFrame()


def main():
    print("=" * 60)
    print("FAO Data Fetcher v4 - Bulk Download com Headers de Navegador")
    print("=" * 60)
    
    # ============================================
    # 1. PRODUÇÃO E COLMEIAS
    # ============================================
    print("\n[1/2] Produção e Colmeias (QCL):")
    
    # Tentar URL principal primeiro
    zip_prod = download_zip(URL_PRODUCTION, "fao_qcl_bulk.zip")
    
    # Se falhar, tentar URL alternativa
    if not zip_prod:
        print("  Tentando servidor alternativo...")
        zip_prod = download_zip(URL_PRODUCTION_ALT, "fao_qcl_bulk_alt.zip")
    
    if zip_prod:
        all_elements = ELEM_PRODUCTION_CODES + ELEM_BEEHIVES_CODES
        df_prod = extract_and_filter(zip_prod, [ITEM_HONEY], all_elements)
        
        if not df_prod.empty:
            output_path = os.path.join(DATA_DIR, "fao_production_raw.csv")
            df_prod.to_csv(output_path, index=False)
            print(f"  [SALVO] {output_path}")
            
            # Estatísticas
            if 'Area' in df_prod.columns:
                print(f"  Países: {df_prod['Area'].nunique()}")
            if 'Year' in df_prod.columns:
                years = sorted(df_prod['Year'].unique())
                print(f"  Período: {min(years)} - {max(years)}")
    else:
        print("  [FALHA] Não foi possível baixar dados de produção.")
    
    # ============================================
    # 2. PREÇOS AO PRODUTOR
    # ============================================
    print("\n[2/2] Preços ao Produtor (PP):")
    
    zip_prices = download_zip(URL_PRICES, "fao_prices_bulk.zip")
    
    if not zip_prices:
        print("  Tentando servidor alternativo...")
        zip_prices = download_zip(URL_PRICES_ALT, "fao_prices_bulk_alt.zip")
    
    if zip_prices:
        df_prices = extract_and_filter(zip_prices, [ITEM_HONEY], ELEM_PRICE_CODES)
        
        if not df_prices.empty:
            output_path = os.path.join(DATA_DIR, "fao_prices_raw.csv")
            df_prices.to_csv(output_path, index=False)
            print(f"  [SALVO] {output_path}")
            
            if 'Area' in df_prices.columns:
                print(f"  Países: {df_prices['Area'].nunique()}")
            if 'Year' in df_prices.columns:
                years = sorted(df_prices['Year'].unique())
                print(f"  Período: {min(years)} - {max(years)}")
    else:
        print("  [FALHA] Não foi possível baixar dados de preços.")
    
    # ============================================
    # RESUMO
    # ============================================
    print("\n" + "=" * 60)
    
    prod_exists = os.path.exists(os.path.join(DATA_DIR, "fao_production_raw.csv"))
    price_exists = os.path.exists(os.path.join(DATA_DIR, "fao_prices_raw.csv"))
    
    if prod_exists or price_exists:
        print("Coleta FAO concluída!")
        if prod_exists:
            print("  ✓ Produção e Colmeias")
        if price_exists:
            print("  ✓ Preços ao Produtor")
    else:
        print("AVISO: Nenhum dado foi coletado.")
        print("Os servidores FAO podem estar bloqueando requisições.")
        print("Verifique os erros acima.")
    print("=" * 60)


if __name__ == "__main__":
    main()
