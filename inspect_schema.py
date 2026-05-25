import sqlite3

conn = sqlite3.connect('mel_export.db')
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

# Check for 'metadata' or 'logs' table
for table in tables:
    if 'metadata' in table[0].lower() or 'log' in table[0].lower():
        print(f"\nSchema for {table[0]}:")
        cursor.execute(f"PRAGMA table_info({table[0]})")
        print(cursor.fetchall())
        
        # Show some rows
        print(f"\nRows in {table[0]}:")
        cursor.execute(f"SELECT * FROM {table[0]} LIMIT 5")
        print(cursor.fetchall())

conn.close()
