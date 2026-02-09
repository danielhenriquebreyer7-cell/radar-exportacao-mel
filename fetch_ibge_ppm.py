import requests
import pandas as pd
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configurações da API do SIDRA
# Tabela 74: Produção de origem animal
# Variável 106: Quantidade produzida (kg)
# Variável 215: Valor da produção (mil reais)
# Classificação 80: Tipo de produto de origem animal -> Categoria 2687: Mel de abelha
PEDIDO_URL_TEMPLATE = "https://servicodados.ibge.gov.br/api/v3/agregados/74/periodos/{periodos}/variaveis/106|215?localidades=N6[N3[{uf_id}]]&classificacao=80[2687]"

# Lista de IDs das UFs (Estados)
UFS = [
    11, 12, 13, 14, 15, 16, 17, # Norte
    21, 22, 23, 24, 25, 26, 27, 28, 29, # Nordeste
    31, 32, 33, 35, # Sudeste
    41, 42, 43, # Sul
    50, 51, 52, 53 # Centro-Oeste
]

DB_NAME = "mel_export.db"

def fetch_uf_data(uf_id, periodos):
    """Função para buscar dados de uma única UF (para uso em thread)."""
    url = PEDIDO_URL_TEMPLATE.format(periodos=periodos, uf_id=uf_id)
    session = requests.Session() # Sessão local da thread
    
    start_time = time.time()
    try:
        response = session.get(url, timeout=90) # Timeout maior
        response.raise_for_status()
        data = response.json()
        
        elapsed = time.time() - start_time
        
        if not data:
            return [], f"UF {uf_id}: Sem dados ({elapsed:.1f}s)"

        temp_dict = {}
        
        for var_item in data:
            var_id = var_item['id'] # 106 ou 215
            
            for res in var_item['resultados']:
                 for serie_item in res['series']:
                     mun_id = serie_item['localidade']['id']
                     mun_nome = serie_item['localidade']['nome']
                     series_data = serie_item['serie']
                     
                     for ano, valor_str in series_data.items():
                         if valor_str == '...' or valor_str == '-':
                             valor_num = 0.0
                         else:
                             try:
                                valor_num = float(valor_str)
                             except:
                                valor_num = 0.0
                         
                         key = (ano, mun_id)
                         if key not in temp_dict:
                             temp_dict[key] = {
                                 'Ano': int(ano),
                                 'Municipio_ID': mun_id,
                                 'Municipio': mun_nome,
                                 'UF_ID': uf_id
                             }
                        
                         if var_id == '106':
                             temp_dict[key]['Producao_Kg'] = valor_num
                         elif var_id == '215':
                             temp_dict[key]['Valor_Prod_MilReais'] = valor_num
        
        records = list(temp_dict.values())
        return records, f"UF {uf_id}: OK ({len(records)} registros em {elapsed:.1f}s)"

    except Exception as e:
        return [], f"UF {uf_id}: ERRO - {str(e)}"

def fetch_ibge_ppm_v2(years=None):
    if years is None:
        periodos = "-10" 
    else:
        periodos = years

    all_data = []
    total_ufs = len(UFS)
    completed = 0
    
    print(f"Iniciando coleta OTIMIZADA do IBGE (PPM - Tabela 74)...")
    print(f"Periodos: {periodos} | UFs: {total_ufs}")
    
    # Executar em paralelo (max 3 threads para não sobrecarregar API)
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_uf = {executor.submit(fetch_uf_data, uf, periodos): uf for uf in UFS}
        
        for future in as_completed(future_to_uf):
            uf = future_to_uf[future]
            try:
                data, msg = future.result()
                completed += 1
                print(f"[{completed}/{total_ufs}] {msg}")
                all_data.extend(data)
            except Exception as exc:
                print(f"UF {uf} gerou exceção não tratada: {exc}")

    if all_data:
        save_to_db(all_data)
    else:
        print("Nenhum dado coletado.")

def save_to_db(data_list):
    print(f"Salvando {len(data_list)} registros no banco de dados...")
    df = pd.DataFrame(data_list)
    
    cols_num = ['Producao_Kg', 'Valor_Prod_MilReais']
    for col in cols_num:
        if col not in df.columns:
            df[col] = 0.0
        else:
            df[col] = df[col].fillna(0.0)
            
    conn = sqlite3.connect(DB_NAME)
    df.to_sql('ibge_ppm', conn, if_exists='replace', index=False)
    
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ibge_ano ON ibge_ppm(Ano)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ibge_mun ON ibge_ppm(Municipio_ID)")
    
    conn.close()
    print("Dados salvos com sucesso na tabela 'ibge_ppm'.")

if __name__ == "__main__":
    fetch_ibge_ppm_v2()
