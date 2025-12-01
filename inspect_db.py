import sqlite3

db_path = r'c:\genefy\database\cattle_breeding.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Tables found:")
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        
        # Get columns for each table
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            
    conn.close()

except Exception as e:
    print(f"Error: {e}")
