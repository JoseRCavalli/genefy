"""
IMPORTAÇÃO COMPLETA - Dados de Fêmeas do Excel
Importa TODAS as 165 colunas do Excel para o banco de dados
"""

import pandas as pd
import sqlite3
from datetime import datetime
import json
import sys

# Configurações
EXCEL_PATH = 'uploads/Females All List - 2025-11-03.xlsx'
DB_PATH = 'database/cattle_breeding.db'

# Mapeamento completo: Excel -> Banco
COLUMN_MAPPING = {
    # Identificação
    'REG ID': 'reg_id',
    'ID': 'internal_id',
    'BDATE': 'birth_date',
    'BREED': 'breed',
    'DATA TYPE': None,  # Vai para genetic_data

    # Genômico
    'gINB': 'genomic_inbreeding',
    'gEFI': 'genomic_future_inbreeding',
    'Test Type': 'test_type',
    'CDCB': 'cdcb',

    # Pedigree
    'SIRE REG': 'sire_reg',
    'SIRE NAAB': 'sire_naab',
    'SIRE NAME': 'sire_name',
    'DAM REG': 'dam_reg',
    'DAM ID': 'dam_id',
    'MGS REG': 'mgs_reg',
    'MGS NAAB': 'mgs_naab',
    'MGS Name': 'mgs_name',

    # Econômicos
    'NET MERIT': 'net_merit',
    'TPI': 'tpi',
    'CHEESE MERIT': 'cheese_merit',
    'FLUID MERIT': 'fluid_merit',
    'GRAZING MERIT': 'grazing_merit',
    'JPI': 'jpi',
    'Eco$': 'eco_dollars',

    # Produção
    'MILK': 'milk',
    'FAT': 'fat',
    'PROTEIN': 'protein',
    'FAT PERCENT': 'fat_percent',
    'PROTEIN PERCENT': 'protein_percent',

    # Funcionalidade
    'PRODUCTIVE LIFE': 'productive_life',
    'SOMATIC CELL SCORE': 'scs',

    # Fertilidade
    'DAUGHTER PREGNANCY RATE': 'dpr',
    'HEIFER CONCEPTION RATE': 'heifer_conception_rate',
    'COW CONCEPTION RATE': 'cow_conception_rate',
    'FERTILITY INDEX': 'fertility_index',
    'EARLY FIRST CALVING': 'early_first_calving',

    # Facilidade de Parto
    'DAUGHTER CALVING EASE': 'daughter_calving_ease',
    'SIRE CALVING EASE': 'sire_calving_ease',
    'DAUGHTER STILLBIRTH': 'daughter_stillbirth',
    'SIRE STILLBIRTH': 'sire_stillbirth',

    # Saúde
    'HEALTH INDEX': 'health_index',
    'HEIFER LIVABILITY': 'heifer_livability',
    'LIVABILITY': 'livability',
    'MASTITITS': 'mastitis',  # Typo no Excel
    'METRITIS': 'metritis',
    'DISPLACED ABOMASUM': 'displaced_abomasum',
    'MILK FEVER': 'milk_fever',
    'RETAINED PLACENTA': 'retained_placenta',
    'KETOSIS': 'ketosis',

    # Tipo/Conformação
    'PTAT': 'ptat',
    'UDC': 'udc',
    'FLC': 'flc',
    'JUI': 'jui',
    'BDE': 'bde',
    'DFM': 'dfm',
    'FLS': 'fls',
    'FTA': 'fta',
    'FTP': 'ftp',
    'FUA': 'fua',
    'RLR': 'rlr',
    'RLS': 'rls',
    'RPA': 'rpa',
    'RTP': 'rtp',
    'RUH': 'ruh',
    'RUW': 'ruw',
    'STA': 'sta',
    'STR': 'str',
    'TLG': 'tlg',
    'TRW': 'trw',
    'UCL': 'ucl',
    'UDP': 'udp',

    # Eficiência
    'FEED EFFICIENCY': 'feed_efficiency',
    'RFI': 'rfi',
    'ECOFEED LIFE': 'ecofeed_life',
    'ECOFEED HEIFER': 'ecofeed_heifer',
    'ECOFEED COW': 'ecofeed_cow',
    'ECO2FEED': 'eco2feed',
    'RCI': 'rci',
    'DOI': 'doi',

    # Genótipos (campos _GV são genotypes values)
    'BCN A2_GV': None,  # Beta Casein - processar especialmente
    'KCN Haplotype_GV': None,  # Kappa Casein - processar especialmente

    # Haplótipos
    'HH1': 'hh1',
    'HH2': 'hh2',
    'HH3': 'hh3',
    'HH4': 'hh4',
    'HH5': 'hh5',
    'HH6': 'hh6',
    'AH1': 'ah1',
    'AH2': 'ah2',
    'JH1': 'jh1',
    'JH2': 'jh2',
    'BH1': 'bh1',
    'BH2': 'bh2',

    # Sustentabilidade
    'VEI': 'vei',
    'VEA': 'vea',
    'BT': 'bt',
    'EMS': 'ems',

    # Outros
    'MILKING SPEED': 'milking_speed',
    'OOC': 'ooc',
}


def safe_float(value):
    """Converte para float de forma segura"""
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_str(value):
    """Converte para string de forma segura"""
    if pd.isna(value):
        return None
    return str(value).strip()


def safe_date(value):
    """Converte para data de forma segura"""
    if pd.isna(value):
        return None
    try:
        if isinstance(value, str):
            # Tentar múltiplos formatos
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                try:
                    return datetime.strptime(value, fmt).strftime('%Y-%m-%d')
                except:
                    continue
        elif isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')
        elif hasattr(value, 'to_pydatetime'):
            return value.to_pydatetime().strftime('%Y-%m-%d')
    except:
        pass
    return None


def process_genotypes(row):
    """Processa genótipos especiais"""
    genotypes = {}

    # Beta Casein
    bcn_field = 'BCN AB_GV' if 'BCN AB_GV' in row else 'BCN A2_GV'
    if bcn_field in row and not pd.isna(row[bcn_field]):
        val = str(row[bcn_field])
        if '2' in val and '1' not in val:
            genotypes['beta_casein'] = 'A2A2'
        elif '2' in val and '1' in val:
            genotypes['beta_casein'] = 'A1A2'
        elif '1' in val:
            genotypes['beta_casein'] = 'A1A1'

    # Kappa Casein
    if 'KCN Haplotype_GV' in row and not pd.isna(row['KCN Haplotype_GV']):
        genotypes['kappa_casein'] = str(row['KCN Haplotype_GV'])

    # Outros genótipos
    for excel_col, db_col in [
        ('BLG BetaLacto Globulin_GV', 'blg_betalacto'),
        ('DGAT_GV', 'dgat'),
        ('Dominant Red_GV', 'dominant_red'),
        ('Red Factor_GV', 'red_factor'),
        ('Slick_GV', 'slick'),
    ]:
        if excel_col in row and not pd.isna(row[excel_col]):
            genotypes[db_col] = str(row[excel_col])

    return genotypes


def import_female(row, cursor):
    """Importa uma fêmea"""
    reg_id = safe_str(row.get('REG ID'))

    if not reg_id:
        return False, "Sem REG ID"

    # Verificar se já existe
    cursor.execute("SELECT id FROM females WHERE reg_id = ?", (reg_id,))
    existing = cursor.fetchone()

    # Preparar dados para colunas dedicadas
    data = {}

    # Mapear colunas
    for excel_col, db_col in COLUMN_MAPPING.items():
        if db_col is None:
            continue

        if excel_col not in row.index:
            continue

        value = row[excel_col]

        # Converter tipo apropriado
        if db_col == 'birth_date':
            data[db_col] = safe_date(value)
        elif db_col in ['reg_id', 'internal_id', 'breed', 'test_type', 'cdcb',
                        'sire_reg', 'sire_naab', 'sire_name', 'dam_reg', 'dam_id',
                        'mgs_reg', 'mgs_naab', 'mgs_name']:
            data[db_col] = safe_str(value)
        else:
            # Numéricos
            data[db_col] = safe_float(value)

    # Processar genótipos
    genotypes = process_genotypes(row)
    data.update(genotypes)

    # Criar genetic_data com campos não mapeados
    genetic_data = {}
    for col in row.index:
        if col not in COLUMN_MAPPING or COLUMN_MAPPING[col] is None:
            if not pd.isna(row[col]):
                genetic_data[col] = safe_float(row[col]) if isinstance(row[col], (int, float)) else str(row[col])

    data['genetic_data'] = json.dumps(genetic_data)

    # Atualizar timestamp
    data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if existing:
        # UPDATE
        female_id = existing[0]

        # Construir SQL UPDATE
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        values = list(data.values()) + [female_id]

        sql = f"UPDATE females SET {set_clause} WHERE id = ?"
        cursor.execute(sql, values)

        return True, f"Atualizada: {reg_id}"
    else:
        # INSERT
        # Adicionar campos obrigatórios
        data['is_active'] = True

        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        values = list(data.values())

        sql = f"INSERT INTO females ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, values)

        return True, f"Inserida: {reg_id}"


def run_import():
    """Executa importação completa"""
    print("=" * 70)
    print("IMPORTACAO COMPLETA - Dados de Femeas")
    print("=" * 70)

    # Verificar arquivo Excel
    print(f"\n[EXCEL] Lendo: {EXCEL_PATH}")
    try:
        df = pd.read_excel(EXCEL_PATH)
        print(f"   Registros: {len(df)}")
        print(f"   Colunas: {len(df.columns)}")
    except Exception as e:
        print(f"[ERRO] Falha ao ler Excel: {e}")
        return False

    # Conectar ao banco
    print(f"\n[DB] Conectando: {DB_PATH}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
    except Exception as e:
        print(f"[ERRO] Falha ao conectar: {e}")
        return False

    # Importar
    print(f"\n[IMPORT] Processando {len(df)} femeas...\n")

    stats = {
        'inserted': 0,
        'updated': 0,
        'errors': 0,
        'skipped': 0
    }

    errors = []

    for idx, row in df.iterrows():
        try:
            success, message = import_female(row, cursor)

            if success:
                if 'Inserida' in message:
                    stats['inserted'] += 1
                elif 'Atualizada' in message:
                    stats['updated'] += 1

                # Mostrar progresso a cada 50
                if (idx + 1) % 50 == 0:
                    print(f"   Processadas: {idx + 1}/{len(df)}")

            else:
                stats['skipped'] += 1
                if len(errors) < 10:
                    errors.append(f"Linha {idx + 1}: {message}")

        except Exception as e:
            stats['errors'] += 1
            if len(errors) < 10:
                errors.append(f"Linha {idx + 1}: {str(e)}")

    # Commit
    try:
        conn.commit()
        print(f"\n[OK] Dados salvos com sucesso!")
    except Exception as e:
        conn.rollback()
        print(f"\n[ERRO] Falha ao salvar: {e}")
        return False

    # Relatório
    print("\n" + "=" * 70)
    print("RELATORIO DE IMPORTACAO")
    print("=" * 70)
    print(f"Total de registros: {len(df)}")
    print(f"  Inseridas:        {stats['inserted']}")
    print(f"  Atualizadas:      {stats['updated']}")
    print(f"  Ignoradas:        {stats['skipped']}")
    print(f"  Erros:            {stats['errors']}")

    if errors:
        print(f"\nPrimeiros erros:")
        for error in errors[:10]:
            print(f"  - {error}")

    # Verificar resultado
    cursor.execute("SELECT COUNT(*) FROM females")
    total = cursor.fetchone()[0]
    print(f"\nTotal no banco: {total} femeas")

    # Verificar alguns campos
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(genomic_inbreeding) as with_ginb,
            COUNT(genomic_future_inbreeding) as with_gefi,
            COUNT(beta_casein) as with_beta,
            COUNT(health_index) as with_health,
            COUNT(feed_efficiency) as with_feed
        FROM females
    """)
    counts = cursor.fetchone()
    print(f"\nCobertura de dados:")
    print(f"  gINB:            {counts[1]}/{counts[0]} ({100*counts[1]/counts[0]:.1f}%)")
    print(f"  gEFI:            {counts[2]}/{counts[0]} ({100*counts[2]/counts[0]:.1f}%)")
    print(f"  Beta Casein:     {counts[3]}/{counts[0]} ({100*counts[3]/counts[0]:.1f}%)")
    print(f"  Health Index:    {counts[4]}/{counts[0]} ({100*counts[4]/counts[0]:.1f}%)")
    print(f"  Feed Efficiency: {counts[5]}/{counts[0]} ({100*counts[5]/counts[0]:.1f}%)")

    conn.close()

    print("\n" + "=" * 70)
    success_rate = (stats['inserted'] + stats['updated']) / len(df) * 100
    if success_rate >= 95:
        print("[OK] Importacao concluida com sucesso!")
        return True
    else:
        print(f"[AVISO] Importacao parcial ({success_rate:.1f}% sucesso)")
        return False


if __name__ == '__main__':
    print("\n")
    success = run_import()
    print("\n" + "=" * 70)

    if success:
        print("[OK] Pronto para atualizar modulo de genetica!")
        print("     Proximo passo: Atualizar backend/services/genetics.py")
    else:
        print("[AVISO] Verifique os erros acima.")

    print("=" * 70 + "\n")
