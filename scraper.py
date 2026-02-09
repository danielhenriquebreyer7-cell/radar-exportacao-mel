import os
import requests
from datetime import datetime

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URLs base do MDIC (Caminhos alternativos que costumam ser mais estáveis para CSVs diretos)
BASE_DATA_URL = "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/mun/EXP_{YEAR}_MUN.csv"
METADATA_URL = "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/tabelas/{NAME}.csv"

METADATA_NAMES = ["PAIS", "MUNICIPIO", "UF", "SH4"]

# Pastas de destino
DATA_DIR = "data"
METADATA_DIR = "metadata"

def download_file(url, target_path):
    print(f"Baixando {url}...")
    try:
        # verify=False para evitar erros de certificado comuns em sites do governo
        response = requests.get(url, stream=True, timeout=30, verify=False)
        response.raise_for_status()
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Salvo em: {target_path}")
        return True
    except Exception as e:
        print(f"Erro ao baixar {url}: {e}")
        return False

def setup():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(METADATA_DIR, exist_ok=True)

def download_metadata():
    for name in METADATA_NAMES:
        url = METADATA_URL.format(NAME=name)
        target = os.path.join(METADATA_DIR, f"{name}.csv")
        # Forçamos o download se o arquivo for HTML (erro anterior)
        if os.path.exists(target):
            with open(target, 'r', errors='ignore') as f:
                first_line = f.readline()
                if "<!DOCTYPE" in first_line or "<html" in first_line.lower():
                    os.remove(target)
                    print(f"Removendo arquivo HTML inválido: {target}")
        
        if not os.path.exists(target):
            download_file(url, target)
        else:
            print(f"Metadado {name} já existe.")

def download_export_data(years):
    for year in years:
        url = BASE_DATA_URL.format(YEAR=year)
        target = os.path.join(DATA_DIR, f"EXP_{year}_MUN.csv")
        if not os.path.exists(target):
            download_file(url, target)
        else:
            print(f"Dados de {year} já existem.")

if __name__ == "__main__":
    setup()
    print("Iniciando download de metadados...")
    download_metadata()
    
    current_year = datetime.now().year
    # Incluindo 2026 conforme solicitado
    years_to_download = [2023, 2024, 2025, 2026]
    
    print(f"Iniciando download de dados de exportação para os anos: {years_to_download}")
    download_export_data(years_to_download)
    print("Processo de download concluído.")
