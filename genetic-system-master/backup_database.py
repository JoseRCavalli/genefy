"""
Script de Backup do Banco de Dados
Cria backup timestamped antes de qualquer modificação
"""

import os
import shutil
from datetime import datetime
import sqlite3

# Configurações
DB_PATH = 'database/cattle_breeding.db'
BACKUP_DIR = 'database/backups'

def create_backup():
    """Cria backup do banco de dados"""

    # Verificar se banco existe
    if not os.path.exists(DB_PATH):
        print(f"[ERRO] Banco de dados nao encontrado: {DB_PATH}")
        return False

    # Criar diretório de backups se não existir
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Nome do backup com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'cattle_breeding_backup_{timestamp}.db'
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    try:
        print(f"[BACKUP] Criando backup do banco de dados...")
        print(f"   Origem: {DB_PATH}")
        print(f"   Destino: {backup_path}")

        # Copiar arquivo
        shutil.copy2(DB_PATH, backup_path)

        # Verificar integridade
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()

        if result[0] == 'ok':
            # Obter tamanho
            size_mb = os.path.getsize(backup_path) / (1024 * 1024)

            print(f"[OK] Backup criado com sucesso!")
            print(f"   Tamanho: {size_mb:.2f} MB")
            print(f"   Integridade: OK")

            # Listar backups existentes
            list_backups()

            return True
        else:
            print(f"[ERRO] Backup corrompido!")
            os.remove(backup_path)
            return False

    except Exception as e:
        print(f"[ERRO] ao criar backup: {e}")
        return False


def list_backups():
    """Lista todos os backups existentes"""
    if not os.path.exists(BACKUP_DIR):
        return

    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')])

    if backups:
        print(f"\n[BACKUPS] Backups existentes ({len(backups)}):")
        for backup in backups:
            backup_path = os.path.join(BACKUP_DIR, backup)
            size_mb = os.path.getsize(backup_path) / (1024 * 1024)
            # Extrair timestamp do nome
            timestamp_str = backup.replace('cattle_breeding_backup_', '').replace('.db', '')
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                date_str = timestamp.strftime('%d/%m/%Y %H:%M:%S')
            except:
                date_str = timestamp_str

            print(f"   - {backup} ({size_mb:.2f} MB) - {date_str}")


def restore_backup(backup_filename):
    """
    Restaura um backup específico
    USO: python backup_database.py restore cattle_breeding_backup_YYYYMMDD_HHMMSS.db
    """
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    if not os.path.exists(backup_path):
        print(f"[ERRO] Backup nao encontrado: {backup_path}")
        return False

    try:
        print(f"[ATENCAO] Isso ira sobrescrever o banco atual!")
        print(f"   Origem: {backup_path}")
        print(f"   Destino: {DB_PATH}")

        response = input("   Confirmar restauracao? (sim/nao): ")
        if response.lower() != 'sim':
            print("[CANCELADO] Restauracao cancelada.")
            return False

        # Criar backup do banco atual antes de restaurar
        print("\n[BACKUP] Criando backup de seguranca do banco atual...")
        create_backup()

        # Restaurar
        print(f"\n[RESTORE] Restaurando backup...")
        shutil.copy2(backup_path, DB_PATH)

        print(f"[OK] Backup restaurado com sucesso!")
        return True

    except Exception as e:
        print(f"[ERRO] ao restaurar backup: {e}")
        return False


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        if len(sys.argv) < 3:
            print("[ERRO] Uso: python backup_database.py restore <backup_filename>")
            list_backups()
        else:
            restore_backup(sys.argv[2])
    else:
        success = create_backup()
        if success:
            print("\n[OK] Pronto para continuar com as migracoes!")
        else:
            print("\n[ERRO] Corrija os erros antes de prosseguir.")
            sys.exit(1)
