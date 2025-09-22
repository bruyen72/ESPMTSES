#!/usr/bin/env python3
"""
Script para adicionar salas adicionais ao banco existente
Mantém todas as salas necessárias para o sistema
"""

from database import conectar

def adicionar_salas_faltantes():
    """Adiciona salas que podem estar faltando no banco"""
    conn = conectar()
    cursor = conn.cursor()

    try:
        print("[INFO] Verificando salas existentes...")

        # Verificar quantas salas existem
        cursor.execute('SELECT COUNT(*) FROM Sala')
        total_salas = cursor.fetchone()[0]
        print(f"[INFO] Salas existentes: {total_salas}")

        # Lista completa de salas necessárias
        salas_necessarias = [
            (1, 'Sala 1', 40),
            (2, 'Sala 2', 40),
            (3, 'Sala 3', 40),
            (4, 'Sala 4', 40),
            (5, 'Sala 5', 40),
            (6, 'Sala 6', 40),
            (7, 'Sala 7', 40),
            (8, 'Sala 8', 40),
            (9, 'Auditório', 150)
        ]

        cursor.execute('BEGIN TRANSACTION')

        salas_adicionadas = 0
        for sala_id, nome, capacidade in salas_necessarias:
            # Verificar se a sala já existe
            cursor.execute('SELECT COUNT(*) FROM Sala WHERE id = ?', (sala_id,))
            existe = cursor.fetchone()[0] > 0

            if not existe:
                # Adicionar sala
                cursor.execute('INSERT INTO Sala (id, nome, capacidade) VALUES (?, ?, ?)',
                             (sala_id, nome, capacidade))
                print(f"[OK] Adicionada: {nome} (capacidade: {capacidade})")
                salas_adicionadas += 1
            else:
                print(f"[OK] Já existe: {nome}")

        cursor.execute('COMMIT')

        if salas_adicionadas > 0:
            print(f"\n[OK] {salas_adicionadas} salas foram adicionadas ao banco!")
        else:
            print(f"\n[OK] Todas as salas já estavam presentes no banco!")

        # Verificar total final
        cursor.execute('SELECT COUNT(*) FROM Sala')
        total_final = cursor.fetchone()[0]
        print(f"[INFO] Total de salas no banco: {total_final}")

        # Listar todas as salas
        print("\n[INFO] Salas disponíveis:")
        cursor.execute('SELECT id, nome, capacidade FROM Sala ORDER BY id')
        salas = cursor.fetchall()
        for sala in salas:
            print(f"  - ID {sala[0]}: {sala[1]} (capacidade: {sala[2]})")

        return True

    except Exception as e:
        cursor.execute('ROLLBACK')
        print(f"[ERRO] Erro ao adicionar salas: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("[INFO] Adicionando salas faltantes...")
    sucesso = adicionar_salas_faltantes()

    if sucesso:
        print("\n[OK] Processo concluído com sucesso!")
    else:
        print("\n[ERRO] Falha no processo!")