#!/usr/bin/env python3
"""
Script de backup dos dados do banco SQLite
Garante que os dados nunca sejam perdidos
"""

import sqlite3
import os
import json
import datetime
from database import conectar, DATABASE

def backup_to_json():
    """Faz backup dos dados em formato JSON"""
    try:
        conn = conectar()
        cursor = conn.cursor()

        backup_data = {}
        backup_data['timestamp'] = datetime.datetime.now().isoformat()
        backup_data['database_path'] = DATABASE

        # Backup das tabelas principais
        tables = ['Users', 'Sala', 'Setor', 'Equipamentos', 'Reservas']

        for table in tables:
            try:
                cursor.execute(f'SELECT * FROM {table}')
                rows = cursor.fetchall()

                # Obter nomes das colunas
                cursor.execute(f'PRAGMA table_info({table})')
                columns = [col[1] for col in cursor.fetchall()]

                # Converter para lista de dicionários
                table_data = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        row_dict[columns[i]] = value
                    table_data.append(row_dict)

                backup_data[table] = table_data
                print(f"[OK] Backup da tabela {table}: {len(table_data)} registros")

            except Exception as e:
                print(f"✗ Erro no backup da tabela {table}: {e}")

        # Salvar backup em arquivo JSON
        backup_filename = f'backup_dados_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"[OK] Backup salvo em: {backup_filename}")
        conn.close()
        return backup_filename

    except Exception as e:
        print(f"[ERRO] Erro no backup: {e}")
        return None

def restore_from_json(backup_file):
    """Restaura dados de um arquivo JSON"""
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)

        conn = conectar()
        cursor = conn.cursor()

        # Restaurar dados de cada tabela
        tables = ['Users', 'Sala', 'Setor', 'Equipamentos', 'Reservas']

        for table in tables:
            if table in backup_data:
                data = backup_data[table]

                for row in data:
                    columns = list(row.keys())
                    values = list(row.values())
                    placeholders = ', '.join(['?' for _ in columns])

                    query = f'INSERT OR REPLACE INTO {table} ({", ".join(columns)}) VALUES ({placeholders})'
                    cursor.execute(query, values)

                print(f"[OK] Restaurados {len(data)} registros da tabela {table}")

        conn.commit()
        conn.close()
        print("[OK] Restore concluido com sucesso!")
        return True

    except Exception as e:
        print(f"[ERRO] Erro no restore: {e}")
        return False

def check_data_integrity():
    """Verifica integridade dos dados"""
    try:
        conn = conectar()
        cursor = conn.cursor()

        # Verificar se as tabelas existem e têm dados
        tables = ['Users', 'Sala', 'Setor', 'Equipamentos', 'Reservas']

        integrity_report = {}
        total_records = 0

        for table in tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                integrity_report[table] = count
                total_records += count
                print(f"[OK] Tabela {table}: {count} registros")
            except Exception as e:
                integrity_report[table] = f"ERRO: {e}"
                print(f"[ERRO] Tabela {table}: ERRO - {e}")

        # Verificar usuário admin
        cursor.execute('SELECT COUNT(*) FROM Users WHERE username = ?', ('admin@ses',))
        admin_exists = cursor.fetchone()[0] > 0

        print(f"\n[INFO] Total de registros: {total_records}")
        print(f"[INFO] Usuario admin existe: {'SIM' if admin_exists else 'NAO'}")
        print(f"[INFO] Localizacao do banco: {DATABASE}")

        conn.close()
        return integrity_report

    except Exception as e:
        print(f"[ERRO] Erro na verificacao: {e}")
        return None

if __name__ == "__main__":
    print("[INFO] Verificando integridade dos dados...")
    check_data_integrity()

    print("\n[INFO] Fazendo backup dos dados...")
    backup_file = backup_to_json()

    if backup_file:
        print(f"\n[OK] Backup concluido: {backup_file}")
    else:
        print("\n[ERRO] Falha no backup!")