import pandas as pd
import sqlite3
import os
import glob

# Configurações
DATA_DIR = "data"
METADATA_DIR = "metadata"
DB_NAME = "mel_export.db"
SH4_CODE = 409  # Mel natural

# Mapeamento SISCOMEX completo (Extraído de fontes oficiais/Fazcomex)
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
        
        # Correção específica para MDIC: Alguns arquivos usam 34 como prefixo para SP
        # Vamos tratar como string para manipulação e depois converter
        df['CO_MUN_STR'] = df['CO_MUN'].astype(str).str.replace('.0', '', regex=False)
        df.loc[df['CO_MUN_STR'].str.startswith('34'), 'CO_MUN_STR'] = '35' + df['CO_MUN_STR'].str[2:]
        df['CO_MUN_FIX'] = pd.to_numeric(df['CO_MUN_STR'], errors='coerce')

        df['SH4'] = pd.to_numeric(df['SH4'], errors='coerce')
        df['CO_PAIS'] = pd.to_numeric(df['CO_PAIS'], errors='coerce')
        
        df_filtered = df[df['SH4'] == SH4_CODE].copy()
        
        if not df_filtered.empty:
            # Mapear Municípios via IBGE usando o código corrigido
            df_filtered = df_filtered.merge(df_ibge, left_on='CO_MUN_FIX', right_on='CO_MUN', how='left')
            
            # Mapear Países via Dicionário Local
            df_filtered['Pais'] = df_filtered['CO_PAIS'].map(COUNTRY_MAPPING).fillna(df_filtered['CO_PAIS'].astype(str))
            
            # Mes Nome
            df_filtered['Mes_Nome'] = df_filtered['CO_MES'].map(MONTH_MAPPING)

            # Fallback para nomes de cidades se o join falhar
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


def process_comtrade_data():
    print("Processando dados globais (Comtrade)...")
    csv_path = os.path.join(DATA_DIR, "comtrade_global_honey_v2.csv")
    
    if not os.path.exists(csv_path):
        print("Arquivo Comtrade não encontrado. Pulando.")
        return

    try:
        df = pd.read_csv(csv_path)
        
        # Selecionar colunas relevantes
        # reporterDesc = País Exportador
        # primaryValue = Valor USD
        # netWgt = Peso KG
        # refYear = Ano
        
        cols_map = {
            'refYear': 'Ano',
            'reporterDesc': 'Pais_Exportador',
            'primaryValue': 'Valor_USD',
            'netWgt': 'Peso_KG'
        }
        
        # Filtrar apenas colunas que existem (segurança)
        available_cols = [c for c in cols_map.keys() if c in df.columns]
        df_filtered = df[available_cols].rename(columns=cols_map)
        
        # Se netWgt não existir, tentar qty
        if 'Peso_KG' not in df_filtered.columns and 'qty' in df.columns:
            df_filtered['Peso_KG'] = df['qty']
            
        # Limpeza básica
        df_filtered['Valor_USD'] = pd.to_numeric(df_filtered['Valor_USD'], errors='coerce').fillna(0)
        
        # Salvar no Banco de Dados
        conn = sqlite3.connect(DB_NAME)
        df_filtered.to_sql('exportacoes_mundo', conn, if_exists='replace', index=False)
        conn.close()
        print(f"Sucesso Global! {len(df_filtered)} registros mundiais atualizados.")
        
    except Exception as e:
        print(f"Erro ao processar Comtrade: {e}")

if __name__ == "__main__":
    process_data()
    process_comtrade_data()
