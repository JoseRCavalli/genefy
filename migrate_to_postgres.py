"""
Script de Migração: SQLite -> PostgreSQL
Copia todos os dados sem alterar nada no código
"""

import os
from sqlalchemy import create_engine, text
from backend.models.database import Base, Female, Bull, Mating, BatchMating, UserPreference, ImportHistory, User
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# SQLite (origem)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, 'database', 'cattle_breeding.db')
SQLITE_URL = f'sqlite:///{SQLITE_PATH}'

POSTGRES_URL = os.environ.get('DATABASE_URL')

if not POSTGRES_URL:
    print("❌ DATABASE_URL não encontrado no .env")
    print("Por favor, adicione a URL do PostgreSQL do Railway no arquivo .env")
    exit(1)

# Correção do URL (postgres:// -> postgresql://)
if POSTGRES_URL.startswith("postgres://"):
    POSTGRES_URL = POSTGRES_URL.replace("postgres://", "postgresql://", 1)

print("=" * 70)
print("MIGRAÇÃO: SQLite -> PostgreSQL")
print("=" * 70)
print(f"Origem:  {SQLITE_URL}")
print(f"Destino: {POSTGRES_URL[:50]}...")
print("=" * 70)

# ============================================================================
# CONEXÕES
# ============================================================================

print("\n1. Conectando aos bancos...")

# SQLite
sqlite_engine = create_engine(SQLITE_URL, echo=False)
print("   ✓ SQLite conectado")

# PostgreSQL
postgres_engine = create_engine(
    POSTGRES_URL, 
    echo=False, 
    pool_pre_ping=True,
    connect_args={
        'sslmode': 'require'
    }
)
print("   ✓ PostgreSQL conectado")

# ============================================================================
# CRIAR TABELAS NO POSTGRESQL
# ============================================================================

print("\n2. Criando estrutura no PostgreSQL...")
Base.metadata.create_all(postgres_engine)
print("   ✓ Tabelas criadas")

# ============================================================================
# MIGRAR DADOS
# ============================================================================

from sqlalchemy.orm import sessionmaker

SQLiteSession = sessionmaker(bind=sqlite_engine)
PostgresSession = sessionmaker(bind=postgres_engine)

sqlite_session = SQLiteSession()
postgres_session = PostgresSession()

def migrate_table(model, name):
    """Migra uma tabela"""
    print(f"\n3. Migrando {name}...")
    
    # Contar no SQLite
    count = sqlite_session.query(model).count()
    print(f"   Registros no SQLite: {count}")
    
    if count == 0:
        print(f"   ⊘ Tabela vazia, pulando")
        return
    
    # Buscar todos os dados
    records = sqlite_session.query(model).all()
    
    # Limpar tabela no Postgres (se existir)
    postgres_session.query(model).delete()
    postgres_session.commit()
    
    # Inserir no PostgreSQL
    for record in records:
        # Criar cópia do objeto
        postgres_session.merge(record)
    
    postgres_session.commit()
    
    # Verificar
    new_count = postgres_session.query(model).count()
    print(f"   ✓ {new_count} registros migrados")

# Ordem de migração (respeitar foreign keys)
tables = [
    (User, "Usuários"),
    (Female, "Fêmeas"),
    (Bull, "Touros"),
    (Mating, "Acasalamentos"),
    (BatchMating, "Lotes"),
    (UserPreference, "Preferências"),
    (ImportHistory, "Histórico de Importações")
]

for model, name in tables:
    try:
        migrate_table(model, name)
    except Exception as e:
        print(f"   ⚠️  Aviso: {str(e)}")

# ============================================================================
# VERIFICAÇÃO FINAL
# ============================================================================

print("\n" + "=" * 70)
print("RESUMO DA MIGRAÇÃO")
print("=" * 70)

for model, name in tables:
    sqlite_count = sqlite_session.query(model).count()
    postgres_count = postgres_session.query(model).count()
    status = "✓" if sqlite_count == postgres_count else "⚠️"
    print(f"{status} {name:30} SQLite: {sqlite_count:5} | PostgreSQL: {postgres_count:5}")

print("=" * 70)

# Fechar conexões
sqlite_session.close()
postgres_session.close()

print("\n✅ Migração concluída!")
print("\nPróximos passos:")
print("1. Verifique se os dados estão corretos no PostgreSQL")
print("2. Faça push do código para o Railway")
print("3. O Railway usará automaticamente o DATABASE_URL do PostgreSQL")
