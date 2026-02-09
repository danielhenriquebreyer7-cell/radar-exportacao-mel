import sqlite3

try:
    conn = sqlite3.connect("mel_export.db")
    cursor = conn.cursor()
    
    print("Verificando dados IBGE (Tabela ibge_ppm)...")
    
    # Contar total
    cursor.execute("SELECT COUNT(*) FROM ibge_ppm")
    total = cursor.fetchone()[0]
    print(f"Total de registros: {total}")
    
    # Amostra por ano
    print("\nResumo por Ano (Top 5):")
    cursor.execute("SELECT Ano, COUNT(*), SUM(Producao_Kg) FROM ibge_ppm GROUP BY Ano ORDER BY Ano DESC LIMIT 5")
    rows = cursor.fetchall()
    
    print(f"{'Ano':<6} | {'Registros':<10} | {'Producao Total (kg)':<20}")
    print("-" * 45)
    for row in rows:
        ano, count, prod = row
        print(f"{ano:<6} | {count:<10} | {prod:,.0f}")
        
    conn.close()
    
except Exception as e:
    print(f"Erro: {e}")
