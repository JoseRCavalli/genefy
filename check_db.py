import sqlite3

conn = sqlite3.connect('database/cattle_breeding.db')
cursor = conn.cursor()

# Listar tabelas
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = [r[0] for r in cursor.fetchall()]
print('Tabelas:', tables)

# Contar fêmeas
cursor.execute('SELECT COUNT(*) FROM females')
print('\nTotal de fêmeas no banco:', cursor.fetchone()[0])

# Estrutura da tabela females
cursor.execute('PRAGMA table_info(females)')
cols = cursor.fetchall()
print(f'\nColunas da tabela females ({len(cols)} colunas):')
for col in cols:
    print(f'  {col[1]}: {col[2]}')

conn.close()
