import pandas as pd
import os
import comtradeapicall

# Configurações
DATA_DIR = "data"
EXPORT_DIR = "analise_exploratoria"
os.makedirs(EXPORT_DIR, exist_ok=True)

INPUT_FILE = os.path.join(DATA_DIR, "comtrade_global_honey_full.csv")
OUTPUT_FILE = os.path.join(EXPORT_DIR, "comtrade_completo_raw.xlsx")

def export_full_data():
    print("Lendo dados brutos...")
    
    dfs = []
    
    # Arquivo de Exportações
    if os.path.exists(INPUT_FILE):
        df_exp = pd.read_csv(INPUT_FILE)
        print(f"Exportações carregadas: {len(df_exp)} registros.")
        dfs.append(df_exp)
    
    # Arquivo de Importações
    IMPORT_FILE = os.path.join(DATA_DIR, "comtrade_global_honey_imports.csv")
    if os.path.exists(IMPORT_FILE):
        df_imp = pd.read_csv(IMPORT_FILE)
        print(f"Importações carregadas: {len(df_imp)} registros.")
        dfs.append(df_imp)
        
    if not dfs:
        print("Nenhum arquivo de dados encontrado.")
        return

    try:
        df_final = pd.concat(dfs, ignore_index=True)
        print(f"Total combinado: {len(df_final)} registros.")

        # Salva em Excel
        print(f"Exportando para {OUTPUT_FILE}...")
        df_final.to_excel(OUTPUT_FILE, index=False, sheet_name="Dados Brutos (Imp+Exp)")
        print("Sucesso!")
        
        # Tenta buscar referências extras para salvar em outra aba
        try:
            print("Buscando tabela de referências de países (Reporters)...")
            refs = comtradeapicall.getReference(category='reporter')
            if refs is not None and not refs.empty:
                 with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl', mode='a') as writer:
                    refs.to_excel(writer, index=False, sheet_name="Metadados Países")
            print("Referência de países adicionada.")
        except Exception as e:
            print(f"Aviso: Não foi possível baixar metadados extras: {e}")

    except Exception as e:
        print(f"Erro ao exportar: {e}")

if __name__ == "__main__":
    export_full_data()
