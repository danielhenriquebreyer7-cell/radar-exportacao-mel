import comtradeapicall
import pandas as pd
import os

# Configurações
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def test_preview_data():
    print("Testando previewFinalData (sem Subscription Key)...")
    try:
        # Parâmetros para Mel Natural (0409)
        # reporterCode='all' ou código específico. Para teste, vamos tentar um país específico ou 'all'
        # flowCode='X' (Export)
        # period='2023'
        
        # previewFinalData(typeCode, freqCode, clCode, period, reporterCode, cmdCode, flowCode, partnerCode, partner2Code, customsCode, motCode, maxRecords=500, format_output='JSON', aggregateBy=None, breakdownMode=None, countOnly=None, includeDesc=True)
        
        df = comtradeapicall.previewFinalData(
            typeCode='C',
            freqCode='A',
            clCode='HS',
            period='2023',
            reporterCode='76', # Brazil
            cmdCode='0409',
            flowCode='X',
            partnerCode='0',
            partner2Code='0',
            customsCode='C00', # Comum para todos os regimes aduaneiros
            motCode='0',       # Comum para todos os meios de transporte
            maxRecords=500
        )
        
        if df is not None and not df.empty:
            print(f"Sucesso! {len(df)} registros baixados via Preview.")
            target_path = os.path.join(DATA_DIR, "comtrade_preview_honey.csv")
            df.to_csv(target_path, index=False)
            print(f"Dados salvos em: {target_path}")
            print("Colunas disponíveis:", df.columns.tolist())
            return True
        else:
            print("Nenhum dado retornado no Preview.")
            return False
            
    except Exception as e:
        print(f"Erro ao testar preview: {e}")
        return False

if __name__ == "__main__":
    test_preview_data()
