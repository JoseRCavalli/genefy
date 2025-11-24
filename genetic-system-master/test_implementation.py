"""
Script de Teste - Validar Implementação Completa
Testa todas as funcionalidades implementadas
"""

import sqlite3
import json

DB_PATH = 'database/cattle_breeding.db'

def test_database_structure():
    """Testa se todas as colunas foram adicionadas"""
    print("=" * 70)
    print("TESTE 1: Estrutura do Banco de Dados")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verificar colunas
    cursor.execute("PRAGMA table_info(females)")
    columns = [row[1] for row in cursor.fetchall()]

    print(f"\nTotal de colunas: {len(columns)}")

    # Verificar colunas críticas
    required_columns = [
        'genomic_future_inbreeding',
        'beta_casein', 'kappa_casein',
        'hh1', 'hh2', 'hh3', 'hh4', 'hh5', 'hh6',
        'health_index', 'mastitis', 'metritis',
        'feed_efficiency', 'rfi',
        'cheese_merit', 'fluid_merit',
        'vei', 'vea', 'eco_dollars'
    ]

    missing = []
    for col in required_columns:
        if col not in columns:
            missing.append(col)

    if missing:
        print(f"\n[ERRO] Colunas faltando: {missing}")
        return False
    else:
        print(f"[OK] Todas as {len(required_columns)} colunas criticas presentes")

    conn.close()
    return True


def test_data_import():
    """Testa se os dados foram importados corretamente"""
    print("\n" + "=" * 70)
    print("TESTE 2: Importacao de Dados")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Contar registros
    cursor.execute("SELECT COUNT(*) FROM females")
    total = cursor.fetchone()[0]
    print(f"\nTotal de femeas: {total}")

    if total == 0:
        print("[ERRO] Nenhuma femea no banco!")
        conn.close()
        return False

    # Verificar cobertura de dados
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(milk) as with_milk,
            COUNT(net_merit) as with_nm,
            COUNT(genomic_inbreeding) as with_ginb,
            COUNT(beta_casein) as with_beta,
            COUNT(health_index) as with_health,
            COUNT(feed_efficiency) as with_feed,
            COUNT(cheese_merit) as with_cheese,
            COUNT(vei) as with_vei
        FROM females
    """)

    counts = cursor.fetchone()
    coverage = {
        'milk': counts[1],
        'net_merit': counts[2],
        'genomic_inbreeding': counts[3],
        'beta_casein': counts[4],
        'health_index': counts[5],
        'feed_efficiency': counts[6],
        'cheese_merit': counts[7],
        'vei': counts[8]
    }

    print(f"\nCobertura de dados:")
    all_good = True
    for field, count in coverage.items():
        pct = (count / counts[0] * 100) if counts[0] > 0 else 0
        status = "[OK]" if pct > 0 else "[VAZIO]"
        print(f"  {status} {field}: {count}/{counts[0]} ({pct:.1f}%)")
        if field in ['milk', 'net_merit', 'genomic_inbreeding'] and pct < 50:
            all_good = False

    # Verificar uma fêmea específica
    cursor.execute("""
        SELECT reg_id, milk, net_merit, tpi, genomic_inbreeding,
               cheese_merit, feed_efficiency, beta_casein, hh1
        FROM females
        LIMIT 1
    """)

    female = cursor.fetchone()
    if female:
        print(f"\nExemplo de femea:")
        print(f"  REG ID: {female[0]}")
        print(f"  MILK: {female[1]}")
        print(f"  NET MERIT: {female[2]}")
        print(f"  TPI: {female[3]}")
        print(f"  gINB: {female[4]}")
        print(f"  Cheese Merit: {female[5]}")
        print(f"  Feed Efficiency: {female[6]}")
        print(f"  Beta Casein: {female[7]}")
        print(f"  HH1: {female[8]}")

    conn.close()

    if all_good:
        print("\n[OK] Dados importados corretamente")
        return True
    else:
        print("\n[AVISO] Alguns campos criticos com baixa cobertura")
        return False


def test_genetics_module():
    """Testa o módulo de genética"""
    print("\n" + "=" * 70)
    print("TESTE 3: Modulo de Genetica")
    print("=" * 70)

    try:
        from backend.services.genetics_complete import genetic_calculator_complete

        print("\n[OK] Modulo genetics_complete importado com sucesso")

        # Criar dados de teste
        female_data = {
            'milk': 1000,
            'protein': 45,
            'fat': 60,
            'net_merit': 500,
            'tpi': 2500,
            'productive_life': 3.5,
            'genomic_inbreeding': 4.0,
            'breed': 'HO',
            'hh1': 0,  # Free
            'hh2': 0,  # Free
        }

        bull_data = {
            'milk': 1500,
            'protein': 55,
            'fat': 70,
            'net_merit': 700,
            'tpi': 2800,
            'productive_life': 5.0,
            'gfi': 5.0,
            'beta_casein': 'A2A2',
            'hh1': 0,  # Free
            'hh2': 0,  # Free
        }

        # Testar PPPV
        print("\nTestando PPPV completo...")
        pppv = genetic_calculator_complete.calculate_pppv_complete(female_data, bull_data)

        if 'production' in pppv and 'milk' in pppv['production']:
            milk_pppv = pppv['production']['milk']['pppv']
            print(f"  [OK] PPPV Milk calculado: {milk_pppv}")
        else:
            print(f"  [ERRO] PPPV Milk nao calculado")
            return False

        # Testar consanguinidade
        print("\nTestando analise de consanguinidade...")
        inbreeding = genetic_calculator_complete.analyze_inbreeding_complete(female_data, bull_data)

        if 'expected_inbreeding' in inbreeding:
            print(f"  [OK] Consanguinidade esperada: {inbreeding['expected_inbreeding']}%")
            print(f"  [OK] Nivel de risco: {inbreeding['risk_level']}")
            print(f"  [OK] Riscos de haplotipo: {len(inbreeding['haplotype_risks'])}")
        else:
            print(f"  [ERRO] Analise de consanguinidade falhou")
            return False

        # Testar compatibilidade
        print("\nTestando score de compatibilidade...")
        compatibility = genetic_calculator_complete.calculate_compatibility_score_complete(
            female_data, bull_data
        )

        if 'score' in compatibility:
            print(f"  [OK] Score: {compatibility['score']}")
            print(f"  [OK] Grade: {compatibility['grade']}")
            print(f"  [OK] Ajustes: {list(compatibility['adjustments'].keys())}")
        else:
            print(f"  [ERRO] Score de compatibilidade falhou")
            return False

        print("\n[OK] Modulo de genetica funcionando corretamente")
        return True

    except Exception as e:
        print(f"\n[ERRO] Falha ao testar modulo de genetica: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_models():
    """Testa os modelos da API"""
    print("\n" + "=" * 70)
    print("TESTE 4: Modelos da API")
    print("=" * 70)

    try:
        from backend.models.database import init_database, get_session, Female

        print("\n[OK] Modelos importados com sucesso")

        # Conectar ao banco
        engine = init_database(f'sqlite:///{DB_PATH}')
        session = get_session(engine)

        # Buscar uma fêmea
        female = session.query(Female).first()

        if not female:
            print("[ERRO] Nenhuma femea encontrada no banco")
            return False

        print(f"\nTestando Female.to_dict()...")

        # Testar versão resumida
        data_simple = female.to_dict(complete=False)
        if 'main_indices' in data_simple:
            print(f"  [OK] Versao resumida: {len(data_simple['main_indices'])} indices principais")
        else:
            print(f"  [ERRO] Versao resumida falhou")
            return False

        # Testar versão completa
        data_complete = female.to_dict(complete=True)
        expected_categories = ['genomic', 'pedigree', 'production', 'economic',
                              'fertility', 'health', 'type', 'efficiency',
                              'calving', 'genotypes', 'haplotypes', 'sustainability']

        missing_categories = []
        for cat in expected_categories:
            if cat not in data_complete:
                missing_categories.append(cat)

        if missing_categories:
            print(f"  [ERRO] Categorias faltando: {missing_categories}")
            return False
        else:
            print(f"  [OK] Versao completa: {len(expected_categories)} categorias")

        # Verificar se tem dados em cada categoria
        print(f"\n  Dados por categoria:")
        for cat in expected_categories:
            count = sum(1 for v in data_complete[cat].values() if v is not None)
            total = len(data_complete[cat])
            print(f"    {cat}: {count}/{total} campos preenchidos")

        session.close()

        print("\n[OK] Modelos da API funcionando corretamente")
        return True

    except Exception as e:
        print(f"\n[ERRO] Falha ao testar modelos: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Executa todos os testes"""
    print("\n")
    print("######################################################################")
    print("#                                                                    #")
    print("#           SUITE DE TESTES - IMPLEMENTACAO COMPLETA                #")
    print("#                                                                    #")
    print("######################################################################")
    print("\n")

    results = {
        'Estrutura do Banco': test_database_structure(),
        'Importacao de Dados': test_data_import(),
        'Modulo de Genetica': test_genetics_module(),
        'Modelos da API': test_api_models()
    }

    # Resumo
    print("\n" + "=" * 70)
    print("RESUMO DOS TESTES")
    print("=" * 70)

    all_passed = True
    for test_name, passed in results.items():
        status = "[OK]" if passed else "[FALHOU]"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("[OK] TODOS OS TESTES PASSARAM!")
        print("\nSistema pronto para uso!")
        print("\nProximos passos:")
        print("  1. Iniciar o servidor: python app.py")
        print("  2. Testar endpoints da API")
        print("  3. Conectar o frontend")
    else:
        print("[ERRO] ALGUNS TESTES FALHARAM")
        print("\nVerifique os erros acima e corrija antes de prosseguir.")

    print("=" * 70 + "\n")

    return all_passed


if __name__ == '__main__':
    run_all_tests()
