import pandas as pd
import sqlite3
import os
import glob
import comtradeapicall

# Configurações
DATA_DIR = "data"
METADATA_DIR = "metadata"
DB_NAME = "mel_export.db"
SH4_CODE = 409  # Mel natural

# Mapeamento SISCOMEX completo
COUNTRY_MAPPING = {
    13: 'Afeganistão', 17: 'Albânia', 23: 'Alemanhã', 31: 'Burkina Faso', 37: 'Andorra',
    40: 'Angola', 41: 'Anguilla', 43: 'Antígua e Barbuda', 53: 'Arábia Saudita', 59: 'Argélia',
    63: 'Argentina', 64: 'Armênia', 65: 'Aruba', 69: 'Austrália', 72: 'Áustria',
    73: 'Azerbaidjão', 77: 'Bahamas', 80: 'Barein', 81: 'Bangladesh', 83: 'Barbados',
    85: 'Belarus', 87: 'Bélgica', 88: 'Belize', 90: 'Bermudas', 93: 'Mianmar',
    97: 'Bolívia', 98: 'Bósnia-Herzegovina', 99: 'Bonaire', 101: 'Botsuana', 105: 'Brasil',
    108: 'Brunei', 111: 'Bulgária', 115: 'Burundi', 119: 'Butão', 127: 'Cabo Verde',
    137: 'Cayman, Ilhas', 141: 'Camboja', 145: 'Camarões', 149: 'Canadá', 153: 'Cazaquistão',
    154: 'Catar', 158: 'Chile', 160: 'China', 161: 'Taiwan', 163: 'Chipre',
    169: 'Colômbia', 173: 'Comores', 177: 'Congo', 183: 'Cook, Ilhas', 187: 'Coreia do Norte',
    190: 'Coreia do Sul', 193: 'Costa do Marfim', 195: 'Croácia', 196: 'Costa Rica',
    199: 'Cuba', 200: 'Curaçao', 229: 'Benin', 232: 'Dinamarca', 235: 'Dominica',
    239: 'Equador', 240: 'Egito', 243: 'Eritreia', 244: 'Emirados Árabes Unidos', 245: 'Espanha',
    246: 'Eslovênia', 247: 'Eslováquia', 249: 'Estados Unidos', 251: 'Estônia', 253: 'Etiópia',
    267: 'Filipinas', 271: 'Finlândia', 275: 'França', 281: 'Gabão', 285: 'Gâmbia',
    289: 'Gana', 291: 'Geórgia', 293: 'Gibraltar', 297: 'Granada', 301: 'Grécia',
    305: 'Groenlândia', 309: 'Guadalupe', 313: 'Guam', 317: 'Guatemala', 325: 'Guiana Francesa',
    329: 'Guiné', 331: 'Guiné-Equatorial', 334: 'Guiné-Bissau', 337: 'Guiana', 341: 'Haiti',
    345: 'Honduras', 351: 'Hong Kong', 355: 'Hungria', 357: 'Iêmen', 359: 'Man, Ilha de',
    361: 'Índia', 365: 'Indonésia', 369: 'Iraque', 372: 'Irã', 375: 'Irlanda',
    379: 'Islândia', 383: 'Israel', 386: 'Itália', 391: 'Jamaica', 399: 'Japão',
    403: 'Jordânia', 411: 'Kiribati', 420: 'Laos', 426: 'Lesoto', 427: 'Letônia',
    431: 'Líbano', 434: 'Libéria', 438: 'Líbia', 440: 'Liechtenstein', 442: 'Lituânia',
    445: 'Luxemburgo', 447: 'Macau', 449: 'Macedônia', 450: 'Madagascar', 455: 'Malásia',
    458: 'Malavi', 461: 'Maldivas', 464: 'Mali', 467: 'Malta', 472: 'Marianas do Norte',
    474: 'Marrocos', 476: 'Marshall, Ilhas', 477: 'Martinica', 485: 'Maurício', 488: 'Mauritânia',
    493: 'México', 494: 'Moldávia', 495: 'Mônaco', 497: 'Mongólia', 498: 'Montenegro',
    499: 'Micronésia', 501: 'Montserrat', 505: 'Moçambique', 507: 'Namíbia', 508: 'Nauru',
    517: 'Nepal', 521: 'Nicarágua', 525: 'Níger', 528: 'Nigéria', 531: 'Niue',
    538: 'Noruega', 542: 'Nova Caledônia', 545: 'Papua Nova Guiné', 548: 'Nova Zelândia',
    551: 'Vanuatu', 556: 'Omã', 573: 'Holanda (Países Baixos)', 575: 'Palau', 576: 'Paquistão',
    578: 'Palestina', 580: 'Panamá', 586: 'Paraguai', 589: 'Peru', 603: 'Polônia',
    607: 'Portugal', 611: 'Porto Rico', 623: 'Quênia', 625: 'Quirguistão', 628: 'Reino Unido',
    640: 'República Centro-Africana', 647: 'República Dominicana', 660: 'Reunião', 665: 'Zimbábue',
    670: 'Romênia', 675: 'Ruanda', 676: 'Rússia', 677: 'Salomão, Ilhas', 687: 'El Salvador',
    690: 'Samoa', 691: 'Samoa Americana', 695: 'São Cristóvão e Névis', 697: 'San Marino',
    705: 'São Vicente e Granadinas', 710: 'Santa Helena', 715: 'Santa Lúcia', 720: 'São Tomé e Príncipe',
    728: 'Senegal', 731: 'Seicheles', 735: 'Serra Leoa', 737: 'Sérvia', 741: 'Cingapura',
    744: 'Síria', 748: 'Somália', 750: 'Sri Lanka', 756: 'África do Sul', 759: 'Sudão',
    760: 'Sudão do Sul', 764: 'Suécia', 767: 'Suíça', 770: 'Suriname', 772: 'Tadjiquistão',
    776: 'Tailândia', 780: 'Tanzânia', 783: 'Djibuti', 788: 'Chade', 791: 'República Tcheca',
    795: 'Timor Leste', 800: 'Togo', 810: 'Tonga', 815: 'Trinidad e Tobago', 820: 'Tunísia',
    827: 'Turquia', 828: 'Tuvalu', 831: 'Ucrânia', 833: 'Uganda', 845: 'Uruguai',
    847: 'Uzbequistão', 848: 'Vaticano', 850: 'Venezuela', 858: 'Vietnã', 870: 'Fiji',
    888: 'Congo, Rep. Democrática', 890: 'Zâmbia'
}

MONTH_MAPPING = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

def read_csv_robust(path, sep=';'):
    for enc in ['utf-8', 'latin-1', 'iso-8859-1']:
        try:
            return pd.read_csv(path, sep=sep, encoding=enc, quotechar='"')
        except Exception:
            continue
    return None

def process_data():
    print("Iniciando processamento refinado...")
    
    # Carregar Municípios do IBGE
    df_ibge = pd.read_csv(os.path.join(METADATA_DIR, "MUNICIPIO_IBGE.csv"), sep=';')
    df_ibge['CO_MUN'] = pd.to_numeric(df_ibge['CO_MUN'], errors='coerce')

    csv_files = glob.glob(os.path.join(DATA_DIR, "EXP_*_MUN.csv"))
    all_data = []

    for file in csv_files:
        print(f"Processando {file}...")
        df = read_csv_robust(file)
        if df is None: continue
        
        # Correção específica para MDIC
        df['CO_MUN_STR'] = df['CO_MUN'].astype(str).str.replace('.0', '', regex=False)
        df.loc[df['CO_MUN_STR'].str.startswith('34'), 'CO_MUN_STR'] = '35' + df['CO_MUN_STR'].str[2:]
        df['CO_MUN_FIX'] = pd.to_numeric(df['CO_MUN_STR'], errors='coerce')

        df['SH4'] = pd.to_numeric(df['SH4'], errors='coerce')
        df['CO_PAIS'] = pd.to_numeric(df['CO_PAIS'], errors='coerce')
        
        df_filtered = df[df['SH4'] == SH4_CODE].copy()
        
        if not df_filtered.empty:
            df_filtered = df_filtered.merge(df_ibge, left_on='CO_MUN_FIX', right_on='CO_MUN', how='left')
            df_filtered['Pais'] = df_filtered['CO_PAIS'].map(COUNTRY_MAPPING).fillna(df_filtered['CO_PAIS'].astype(str))
            df_filtered['Mes_Nome'] = df_filtered['CO_MES'].map(MONTH_MAPPING)

            df_filtered['Municipio'] = df_filtered['NO_MUN'].fillna(df_filtered['CO_MUN_FIX'].astype(str))
            df_filtered['UF'] = df_filtered['SG_UF'].fillna(df_filtered['SG_UF_MUN'])

            final_cols = {
                'CO_ANO': 'Ano',
                'Mes_Nome': 'Mes',
                'Municipio': 'Municipio',
                'UF': 'UF',
                'Pais': 'Pais',
                'VL_FOB': 'Valor_USD',
                'KG_LIQUIDO': 'Peso_KG',
                'CO_MES': 'Mes_Num'
            }
            
            df_final = df_filtered[list(final_cols.keys())].rename(columns=final_cols)
            all_data.append(df_final)
            print(f"  {len(df_final)} registros processados.")

    if all_data:
        consolidated_df = pd.concat(all_data, ignore_index=True)
        conn = sqlite3.connect(DB_NAME)
        consolidated_df.to_sql('exportacoes_mel', conn, if_exists='replace', index=False)
        conn.close()
        print(f"Sucesso! {len(consolidated_df)} registros atualizados.")
    else:
        print("Nenhum dado encontrado.")

def get_comtrade_country_map(subscription_key):
    """Obtém mapa de códigos de países da Comtrade."""
    print("Obtendo metadados de países (Reporters)...")
    try:
        df_refs = comtradeapicall.getReference(category='reporter')
        
        if df_refs is not None and not df_refs.empty:
             # id -> text mapping
             return dict(zip(df_refs['id'], df_refs['text']))
    except Exception as e:
        print(f"Erro ao obter metadados: {e}")
    return {}

def process_comtrade_data(subscription_key):
    print("\nProcessando dados globais (Comtrade)...")
    
    files_to_process = [
        ("comtrade_global_honey_full.csv", "Export"),
        ("comtrade_global_honey_imports.csv", "Import")
    ]
    
    all_data = []
    country_map = None # Cache for metadata

    for filename, flow_type in files_to_process:
        source_file = os.path.join(DATA_DIR, filename)
        if not os.path.exists(source_file):
            print(f"Arquivo {filename} não encontrado. Pulando.")
            continue
            
        print(f"Lendo {filename}...")
        df = pd.read_csv(source_file)
        
        # Mapear Países se reporterDesc estiver vazio ou numérico
        if 'reporterDesc' not in df.columns or df['reporterDesc'].isna().all() or (df['reporterDesc'] == '').all() or df['reporterDesc'].dtype != object:
            if country_map is None:
                print("Buscando metadados de países...")
                country_map = get_comtrade_country_map(subscription_key)
            
            df['reporterCode'] = pd.to_numeric(df['reporterCode'], errors='coerce')
            df['reporterDesc'] = df['reporterCode'].map(country_map)
            
        # Garantir que temos a coluna de fluxo
        df['Tipo'] = flow_type
        
        # Seleção de colunas
        cols_map = {
            'period': 'Ano',
            'reporterDesc': 'Pais',
            'cmdCode': 'HS_Code',
            'primaryValue': 'Valor_USD',
            'netWgt': 'Peso_KG',
            'Tipo': 'Tipo'
        }
        
        # Verificar quais colunas existem no DF original (segurança)
        available_cols = [c for c in cols_map.keys() if c in df.columns or c == 'Tipo']
        df_final = df[available_cols].rename(columns=cols_map)
        
        all_data.append(df_final)

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df['Ano'] = pd.to_numeric(combined_df['Ano'], errors='coerce')
        combined_df['Valor_USD'] = pd.to_numeric(combined_df['Valor_USD'], errors='coerce').fillna(0)
        combined_df['Peso_KG'] = pd.to_numeric(combined_df['Peso_KG'], errors='coerce').fillna(0)
        
        conn = sqlite3.connect(DB_NAME)
        combined_df.to_sql('comtrade_data', conn, if_exists='replace', index=False)
        print(f"Sucesso! {len(combined_df)} registros globais (Exp+Imp) processados.")
        
        # --- PROCESSAMENTO BILATERAL ---
        bilateral_file = os.path.join(DATA_DIR, "comtrade_bilateral_raw.csv")
        if os.path.exists(bilateral_file):
            print("Processando dados bilaterais...")
            df_bil = pd.read_csv(bilateral_file)
            
            # Garantir mappings
            if 'reporterDesc' not in df_bil.columns or df_bil['reporterDesc'].isna().any():
                if country_map is None: country_map = get_comtrade_country_map(subscription_key)
                df_bil['reporterDesc'] = df_bil['reporterCode'].map(country_map).fillna(df_bil['reporterDesc'])
            
            # Partner pode não ter desc, vamos tentar mapear também
            if 'partnerDesc' not in df_bil.columns or df_bil['partnerDesc'].isna().any():
                 if country_map is None: country_map = get_comtrade_country_map(subscription_key)
                 df_bil['partnerDesc'] = df_bil['partnerCode'].map(country_map).fillna(df_bil['partnerDesc'])

            # Selecionar colunas
            df_bil_final = df_bil[['period', 'reporterDesc', 'partnerDesc', 'primaryValue', 'netWgt']].copy()
            df_bil_final.columns = ['Ano', 'Origem', 'Destino', 'Valor_USD', 'Peso_KG']
            
            df_bil_final['Valor_USD'] = pd.to_numeric(df_bil_final['Valor_USD'], errors='coerce').fillna(0)
            df_bil_final['Peso_KG'] = pd.to_numeric(df_bil_final['Peso_KG'], errors='coerce').fillna(0)
            
            # Salvar tabela separada
            df_bil_final.to_sql('comtrade_bilateral', conn, if_exists='replace', index=False)
            print(f"Sucesso! {len(df_bil_final)} fluxos bilaterais salvos.")
            
        # --- PROCESSAMENTO MENSAL (SAZONALIDADE) ---
        monthly_file = os.path.join(DATA_DIR, "comtrade_monthly_raw.csv")
        if os.path.exists(monthly_file):
            print("Processando dados mensais...")
            df_monthly = pd.read_csv(monthly_file)
            
            # Garantir mappings
            if 'reporterDesc' not in df_monthly.columns or df_monthly['reporterDesc'].isna().any():
                if country_map is None: country_map = get_comtrade_country_map(subscription_key)
                df_monthly['reporterDesc'] = df_monthly['reporterCode'].map(country_map).fillna(df_monthly['reporterDesc'])
            
            # Selecionar colunas
            # period mensal vem como 202301 (int). Vamos quebrar.
            df_monthly['period'] = df_monthly['period'].astype(str)
            df_monthly['Ano'] = df_monthly['period'].str[:4].astype(int)
            df_monthly['Mes'] = df_monthly['period'].str[4:].astype(int)
            
            df_mensal_final = df_monthly[['Ano', 'Mes', 'reporterDesc', 'Tipo', 'primaryValue', 'netWgt']].copy()
            df_mensal_final.columns = ['Ano', 'Mes', 'Pais', 'Tipo', 'Valor_USD', 'Peso_KG']
            
            df_mensal_final['Valor_USD'] = pd.to_numeric(df_mensal_final['Valor_USD'], errors='coerce').fillna(0)
            df_mensal_final['Peso_KG'] = pd.to_numeric(df_mensal_final['Peso_KG'], errors='coerce').fillna(0)
            
            df_mensal_final.to_sql('comtrade_mensal', conn, if_exists='replace', index=False)
            print(f"Sucesso! {len(df_mensal_final)} registros mensais salvos.")
            
        # --- PROCESSAMENTO FAO (NOVO) ---
        print("Processando dados FAO...")
        
        # 1. Produção e Colmeias
        fao_prod_file = os.path.join(DATA_DIR, "fao_production_honey.csv")
        if os.path.exists(fao_prod_file):
            df_prod = pd.read_csv(fao_prod_file)
            # Colunas: Area Code, Area, Element Code, Year, Value
            
            # 1. Filtro de Agregados Regionais (Area Code < 5000)
            df_prod = df_prod[df_prod['Area Code'] < 5000]
            
            # 2. Pivotar para unir Production e Stocks
            # Mapear Element Code: 5510 -> Producao_Ton, 5111 -> Colmeias
            elem_map = {5510: 'Producao_Ton', 5111: 'Colmeias'}
            df_prod['Type'] = df_prod['Element Code'].map(elem_map)
            df_prod = df_prod.dropna(subset=['Type'])
            
            df_pivoted_prod = df_prod.pivot_table(
                index=['Area', 'Year'], 
                columns='Type', 
                values='Value', 
                aggfunc='first'
            ).reset_index()
            
            # Garantir colunas
            if 'Producao_Ton' not in df_pivoted_prod.columns: df_pivoted_prod['Producao_Ton'] = 0
            if 'Colmeias' not in df_pivoted_prod.columns: df_pivoted_prod['Colmeias'] = 0
            
            # 3. Calcular Yield (Kg/Colmeia)
            # Yield = (Ton * 1000) / Colmeias
            df_pivoted_prod['Yield_Hg'] = 0 # Placeholder se quisesse Hg (padrão FAO), mas vamos usar Kg
            df_pivoted_prod['Yield_Kg_Colmeia'] = df_pivoted_prod.apply(
                lambda row: (row['Producao_Ton'] * 1000) / row['Colmeias'] if row['Colmeias'] > 0 else 0, axis=1
            )

            # Renomear para banco
            df_pivoted_prod = df_pivoted_prod.rename(columns={'Area': 'Pais', 'Year': 'Ano'})
            
            df_pivoted_prod.to_sql('fao_production', conn, if_exists='replace', index=False)
            print(f"Sucesso! {len(df_pivoted_prod)} registros de produção/colmeias FAO salvos.")
            
        # 2. Preços
        fao_price_file = os.path.join(DATA_DIR, "fao_prices_honey.csv")
        if os.path.exists(fao_price_file):
            df_prices = pd.read_csv(fao_price_file)
            
            # Filtro de Agregados
            df_prices = df_prices[df_prices['Area Code'] < 5000]
            
            # Element Code 5530 (LCU), 5532 (USD)
            elem_map = {5530: 'Price_LCU', 5532: 'Price_USD'}
            df_prices['Type'] = df_prices['Element Code'].map(elem_map)
            
            # Pivot
            df_pivoted = df_prices.pivot_table(
                index=['Area', 'Year'], 
                columns='Type', 
                values='Value', 
                aggfunc='first'
            ).reset_index()
            
            # Renomear
            df_pivoted = df_pivoted.rename(columns={'Area': 'Pais', 'Year': 'Ano'})
            
            # Salvar
            df_pivoted.to_sql('fao_prices', conn, if_exists='replace', index=False)
            print(f"Sucesso! {len(df_pivoted)} registros de preços FAO salvos.")

        conn.close()

    else:
        print("Nenhum dado global processado.")

if __name__ == "__main__":
    process_data()
    SUBSCRIPTION_KEY = "6383e7fcf14b4f48a842339b9a6fe4f6" 
    process_comtrade_data(SUBSCRIPTION_KEY)
