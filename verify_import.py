import sqlite3

db_path = r'c:\genefy\database\cattle_breeding.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM females")
    females_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bulls")
    bulls_count = cursor.fetchone()[0]
    
    print(f"Females count: {females_count}")
    print(f"Bulls count: {bulls_count}")
    
    # Check a specific record
    cursor.execute("SELECT * FROM females WHERE reg_id = '10008'")
    female = cursor.fetchone()
    if female:
        print("\nFemale 10008 found:")
        print(f"  Name: {female[3]}")
        print(f"  Milk: {female[7]}")
        print(f"  Net Merit: {female[17]}")
    else:
        print("\nFemale 10008 NOT found.")

    cursor.execute("SELECT * FROM bulls WHERE code = '14HO17426'")
    bull = cursor.fetchone()
    if bull:
        print("\nBull 14HO17426 found:")
        print(f"  Name: {bull[2]}")
        print(f"  Milk: {bull[7]}")
        print(f"  Net Merit: {bull[12]}")
    else:
        print("\nBull 14HO17426 NOT found.")
            
    conn.close()

except Exception as e:
    print(f"Error: {e}")
