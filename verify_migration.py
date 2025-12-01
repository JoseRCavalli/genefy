"""
Verificar dados migrados no PostgreSQL
"""

import os
from sqlalchemy import create_engine
from backend.models.database import Female, Bull, Mating, User
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

POSTGRES_URL = "postgresql://postgres:CIRpWlpQBQpehchYTFqgXkLNtHvoCVIK@gondola.proxy.rlwy.net:42845/railway"

# Conectar
engine = create_engine(
    POSTGRES_URL, 
    echo=False,
    connect_args={'sslmode': 'require'}
)

Session = sessionmaker(bind=engine)
session = Session()

print("=" * 70)
print("VERIFICAÇÃO DO POSTGRESQL")
print("=" * 70)

# Contar registros
tables = [
    (Female, "Fêmeas"),
    (Bull, "Touros"),
    (Mating, "Acasalamentos"),
    (User, "Usuários")
]

for model, name in tables:
    try:
        count = session.query(model).count()
        print(f"{name:30} {count:5} registros")
    except Exception as e:
        print(f"{name:30} ⚠️ Erro: {str(e)}")

print("=" * 70)

# Mostrar algumas fêmeas
print("\nPrimeiras 5 fêmeas:")
females = session.query(Female).limit(5).all()
for f in females:
    print(f"  - {f.reg_id or f.internal_id}: {f.name}")

print("\nPrimeiros 5 touros:")
bulls = session.query(Bull).limit(5).all()
for b in bulls:
    print(f"  - {b.code}: {b.name}")

session.close()
print("\n✅ Verificação concluída!")
