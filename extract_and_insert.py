import json
import sqlite3
import re
import os
from datetime import datetime

DB_PATH = r'c:\genefy\database\cattle_breeding.db'
RAW_DATA_PATH = r'c:\genefy\raw_data.txt'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return None

def insert_female(cursor, data):
    # Map fields
    reg_id = str(data.get("REG ID", "")).replace(".0", "")
    internal_id = str(data.get("ID", "")).replace(".0", "")
    name = data.get("ID", "") # Using ID as name if name not present, or maybe just ID
    birth_date = parse_date(data.get("BDATE"))
    breed = data.get("BREED")
    
    # Metrics
    milk = data.get("MILK")
    protein = data.get("PROTEIN")
    fat = data.get("FAT")
    pl = data.get("PRODUCTIVE LIFE")
    scs = data.get("SOMATIC CELL SCORE")
    dpr = data.get("DAUGHTER PREGNANCY RATE")
    fi = data.get("FERTILITY INDEX")
    udc = data.get("UDC")
    flc = data.get("FLC")
    ptat = data.get("PTAT")
    nm = data.get("NET MERIT")
    tpi = data.get("TPI")
    ginb = data.get("gINB")
    
    genetic_data = json.dumps(data)
    
    # Check if exists
    cursor.execute("SELECT id FROM females WHERE reg_id = ?", (reg_id,))
    exists = cursor.fetchone()
    
    if exists:
        print(f"Updating female {reg_id}")
        cursor.execute("""
            UPDATE females SET
                internal_id = ?, birth_date = ?, breed = ?, milk = ?, protein = ?, fat = ?,
                productive_life = ?, scs = ?, dpr = ?, fertility_index = ?, udc = ?, flc = ?,
                ptat = ?, net_merit = ?, tpi = ?, genomic_inbreeding = ?, genetic_data = ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE reg_id = ?
        """, (internal_id, birth_date, breed, milk, protein, fat, pl, scs, dpr, fi, udc, flc, ptat, nm, tpi, ginb, genetic_data, reg_id))
    else:
        print(f"Inserting female {reg_id}")
        cursor.execute("""
            INSERT INTO females (
                reg_id, internal_id, name, birth_date, breed, milk, protein, fat,
                productive_life, scs, dpr, fertility_index, udc, flc, ptat,
                net_merit, tpi, genomic_inbreeding, genetic_data, last_updated, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
        """, (reg_id, internal_id, str(internal_id), birth_date, breed, milk, protein, fat, pl, scs, dpr, fi, udc, flc, ptat, nm, tpi, ginb, genetic_data))

def insert_bull(cursor, data):
    code = data.get("code")
    name = data.get("name")
    
    milk = data.get("milk")
    protein = data.get("protein")
    fat = data.get("fat")
    nm = data.get("net_merit")
    cm = data.get("cheese_merit")
    gm = data.get("grazing_merit")
    udc = data.get("udc")
    flc = data.get("flc")
    ptat = data.get("ptat")
    scs = data.get("scs")
    dpr = data.get("dpr")
    fi = data.get("fertility_index")
    rfi = data.get("rfi")
    gfi = data.get("gfi")
    
    genetic_data = json.dumps(data)
    
    cursor.execute("SELECT id FROM bulls WHERE code = ?", (code,))
    exists = cursor.fetchone()
    
    if exists:
        print(f"Updating bull {code}")
        cursor.execute("""
            UPDATE bulls SET
                name = ?, milk = ?, protein = ?, fat = ?, net_merit = ?, cheese_merit = ?,
                grazing_merit = ?, udc = ?, flc = ?, ptat = ?, scs = ?, dpr = ?,
                fertility_index = ?, rfi = ?, gfi = ?, genetic_data = ?, last_updated = CURRENT_TIMESTAMP
            WHERE code = ?
        """, (name, milk, protein, fat, nm, cm, gm, udc, flc, ptat, scs, dpr, fi, rfi, gfi, genetic_data, code))
    else:
        print(f"Inserting bull {code}")
        cursor.execute("""
            INSERT INTO bulls (
                code, name, milk, protein, fat, net_merit, cheese_merit, grazing_merit,
                udc, flc, ptat, scs, dpr, fertility_index, rfi, gfi, genetic_data,
                last_updated, is_available
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
        """, (code, name, milk, protein, fat, nm, cm, gm, udc, flc, ptat, scs, dpr, fi, rfi, gfi, genetic_data))

def main():
    if not os.path.exists(RAW_DATA_PATH):
        print(f"File not found: {RAW_DATA_PATH}")
        return

    print("Reading raw data...")
    with open(RAW_DATA_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Extract JSONs
    # Pattern: Look for { ... }
    # Since we have mixed content, we'll try to find starts and matching ends
    json_objects = []
    decoder = json.JSONDecoder()
    pos = 0
    while True:
        match = content.find('{', pos)
        if match == -1:
            break
        try:
            obj, idx = decoder.raw_decode(content[match:])
            json_objects.append(obj)
            pos = match + idx
        except json.JSONDecodeError:
            pos = match + 1
            
    print(f"Found {len(json_objects)} JSON objects.")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    count_females = 0
    count_bulls = 0
    
    try:
        for obj in json_objects:
            if "REG ID" in obj:
                insert_female(cursor, obj)
                count_females += 1
            elif "code" in obj:
                insert_bull(cursor, obj)
                count_bulls += 1
            else:
                print(f"Unknown object type: {obj.keys()}")
        
        conn.commit()
        print(f"Successfully processed {count_females} females and {count_bulls} bulls.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during import: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
