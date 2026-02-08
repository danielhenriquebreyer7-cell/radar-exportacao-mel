"""
FAO Data Processor - Processa os CSVs baixados manualmente do FAOSTAT
Cria as tabelas necessárias no banco de dados SQLite.
"""
import pandas as pd
import sqlite3
import os
import glob

# Configurações
DATA_DIR = "data"
DB_NAME = "mel_export.db"


def process_fao_production():
    """Processa dados de produção (QCL - Crops and livestock products)."""
    print("\n[1/4] Processando Produção FAO (QCL)...")
    
    # Encontrar arquivo de produção
    files = glob.glob(os.path.join(DATA_DIR, "FAOSTAT_data_en_*.csv"))
    
    prod_file = None
    for f in files:
        try:
            df_check = pd.read_csv(f, nrows=5, encoding='utf-8-sig')
            if 'Domain Code' in df_check.columns and df_check['Domain Code'].iloc[0] == 'QCL':
                if 'Production' in df_check['Element'].values:
                    prod_file = f
                    break
        except Exception:
            continue
    
    if not prod_file:
        print("  [AVISO] Arquivo de produção (QCL) não encontrado.")
        return pd.DataFrame()
    
    print(f"  Arquivo: {os.path.basename(prod_file)}")
    df = pd.read_csv(prod_file, encoding='utf-8-sig')
    
    # Padronizar colunas
    df = df.rename(columns={
        'Area': 'Pais',
        'Year': 'Ano',
        'Value': 'Producao_Ton',
        'Element': 'Tipo',
        'Element Code': 'Element_Code'
    })
    
    # Filtrar apenas produção (Element Code 5510)
    df = df[df['Element_Code'] == 5510].copy()
    
    # Converter Ton para Kg
    df['Producao_Kg'] = df['Producao_Ton'] * 1000
    
    # Selecionar colunas relevantes
    df_final = df[['Pais', 'Ano', 'Producao_Ton', 'Producao_Kg']].copy()
    df_final = df_final.dropna(subset=['Producao_Ton'])
    
    print(f"  [OK] {len(df_final)} registros processados.")
    return df_final


def process_fao_value():
    """Processa dados de valor da produção (QV)."""
    print("\n[2/4] Processando Valor da Produção FAO (QV)...")
    
    files = glob.glob(os.path.join(DATA_DIR, "FAOSTAT_data_en_*.csv"))
    
    value_file = None
    for f in files:
        try:
            df_check = pd.read_csv(f, nrows=5, encoding='utf-8-sig')
            if 'Domain Code' in df_check.columns and df_check['Domain Code'].iloc[0] == 'QV':
                value_file = f
                break
        except Exception:
            continue
    
    if not value_file:
        print("  [AVISO] Arquivo de valor (QV) não encontrado.")
        return pd.DataFrame()
    
    print(f"  Arquivo: {os.path.basename(value_file)}")
    df = pd.read_csv(value_file, encoding='utf-8-sig')
    
    df = df.rename(columns={
        'Area': 'Pais',
        'Year': 'Ano',
        'Value': 'Valor_1000_IntDollar',
        'Element': 'Tipo'
    })
    
    df_final = df[['Pais', 'Ano', 'Valor_1000_IntDollar', 'Tipo']].copy()
    df_final = df_final.dropna(subset=['Valor_1000_IntDollar'])
    
    print(f"  [OK] {len(df_final)} registros processados.")
    return df_final


def process_fao_trade():
    """Processa dados de comércio (TCL - Trade Crops Livestock)."""
    print("\n[3/4] Processando Comércio FAO (TCL)...")
    
    files = glob.glob(os.path.join(DATA_DIR, "FAOSTAT_data_en_*.csv"))
    
    trade_file = None
    for f in files:
        try:
            df_check = pd.read_csv(f, nrows=5, encoding='utf-8-sig')
            if 'Domain Code' in df_check.columns and df_check['Domain Code'].iloc[0] == 'TCL':
                trade_file = f
                break
        except Exception:
            continue
    
    if not trade_file:
        print("  [AVISO] Arquivo de comércio (TCL) não encontrado.")
        return pd.DataFrame()
    
    print(f"  Arquivo: {os.path.basename(trade_file)}")
    df = pd.read_csv(trade_file, encoding='utf-8-sig')
    
    df = df.rename(columns={
        'Area': 'Pais',
        'Year': 'Ano',
        'Value': 'Valor',
        'Element': 'Tipo',
        'Element Code': 'Element_Code',
        'Unit': 'Unidade'
    })
    
    # Mapear elementos:
    # 5610 = Import quantity (t)
    # 5622 = Import value (1000 USD)
    # 5910 = Export quantity (t)
    # 5922 = Export value (1000 USD)
    element_map = {
        5610: 'Import_Qty_Ton',
        5622: 'Import_Value_1000USD',
        5910: 'Export_Qty_Ton',
        5922: 'Export_Value_1000USD'
    }
    
    df['Metrica'] = df['Element_Code'].map(element_map)
    df = df.dropna(subset=['Metrica', 'Valor'])
    
    # Pivotar para ter colunas separadas
    df_pivot = df.pivot_table(
        index=['Pais', 'Ano'],
        columns='Metrica',
        values='Valor',
        aggfunc='first'
    ).reset_index()
    
    # Preencher NaN com 0
    for col in ['Import_Qty_Ton', 'Import_Value_1000USD', 'Export_Qty_Ton', 'Export_Value_1000USD']:
        if col not in df_pivot.columns:
            df_pivot[col] = 0
        else:
            df_pivot[col] = df_pivot[col].fillna(0)
    
    # Calcular balança comercial
    df_pivot['Balanca_1000USD'] = df_pivot['Export_Value_1000USD'] - df_pivot['Import_Value_1000USD']
    df_pivot['Balanca_Ton'] = df_pivot['Export_Qty_Ton'] - df_pivot['Import_Qty_Ton']
    
    print(f"  [OK] {len(df_pivot)} registros processados.")
    return df_pivot


def process_fao_indices():
    """Processa índices de comércio (TI - Trade Indices)."""
    print("\n[4/4] Processando Índices de Comércio FAO (TI)...")
    
    files = glob.glob(os.path.join(DATA_DIR, "FAOSTAT_data_en_*.csv"))
    
    index_file = None
    for f in files:
        try:
            df_check = pd.read_csv(f, nrows=5, encoding='utf-8-sig')
            if 'Domain Code' in df_check.columns and df_check['Domain Code'].iloc[0] == 'TI':
                index_file = f
                break
        except Exception:
            continue
    
    if not index_file:
        print("  [AVISO] Arquivo de índices (TI) não encontrado.")
        return pd.DataFrame()
    
    print(f"  Arquivo: {os.path.basename(index_file)}")
    df = pd.read_csv(index_file, encoding='utf-8-sig')
    
    df = df.rename(columns={
        'Area': 'Pais',
        'Year': 'Ano',
        'Value': 'Indice',
        'Element': 'Tipo',
        'Element Code': 'Element_Code'
    })
    
    # Mapear elementos:
    # 462 = Import Value Index
    # 464 = Export Value Index
    # 466 = Import Quantity Index
    # 468 = Export Quantity Index
    element_map = {
        462: 'Import_Value_Index',
        464: 'Export_Value_Index',
        466: 'Import_Qty_Index',
        468: 'Export_Qty_Index'
    }
    
    df['Metrica'] = df['Element_Code'].map(element_map)
    df = df.dropna(subset=['Metrica', 'Indice'])
    
    # Pivotar
    df_pivot = df.pivot_table(
        index=['Pais', 'Ano'],
        columns='Metrica',
        values='Indice',
        aggfunc='first'
    ).reset_index()
    
    print(f"  [OK] {len(df_pivot)} registros processados.")
    return df_pivot


def save_to_database(df_prod, df_value, df_trade, df_indices):
    """Salva todos os DataFrames no banco SQLite."""
    print("\n[SAVE] Salvando no banco de dados...")
    
    conn = sqlite3.connect(DB_NAME)
    
    if not df_prod.empty:
        df_prod.to_sql('fao_production_new', conn, if_exists='replace', index=False)
        print(f"  ✓ fao_production_new: {len(df_prod)} registros")
    
    if not df_value.empty:
        df_value.to_sql('fao_value', conn, if_exists='replace', index=False)
        print(f"  ✓ fao_value: {len(df_value)} registros")
    
    if not df_trade.empty:
        df_trade.to_sql('fao_trade', conn, if_exists='replace', index=False)
        print(f"  ✓ fao_trade: {len(df_trade)} registros")
    
    if not df_indices.empty:
        df_indices.to_sql('fao_indices', conn, if_exists='replace', index=False)
        print(f"  ✓ fao_indices: {len(df_indices)} registros")
    
    conn.close()
    print("\n[OK] Dados FAO salvos com sucesso!")


def main():
    print("=" * 60)
    print("FAO Data Processor - Arquivos Manuais")
    print("=" * 60)
    
    # Processar cada tipo de dado
    df_prod = process_fao_production()
    df_value = process_fao_value()
    df_trade = process_fao_trade()
    df_indices = process_fao_indices()
    
    # Salvar no banco
    save_to_database(df_prod, df_value, df_trade, df_indices)
    
    print("\n" + "=" * 60)
    print("Processamento concluído!")
    print("=" * 60)


if __name__ == "__main__":
    main()
