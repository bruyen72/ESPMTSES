#!/usr/bin/env python3
"""
Script de inicialização do banco de dados para produção
Este script garante que o banco de dados seja criado e inicializado corretamente
"""

import os
import sys
from database import criar_tabelas, adicionar_usuario, buscar_usuario

def init_database():
    """Inicializa o banco de dados e cria o usuário admin padrão"""
    try:
        print("Inicializando banco de dados...")

        # Criar todas as tabelas
        criar_tabelas()
        print("✓ Tabelas criadas com sucesso")

        # Verificar se o usuário admin já existe
        admin_user = buscar_usuario('admin@ses')
        if not admin_user:
            # Criar usuário admin padrão
            success, message = adicionar_usuario('admin@ses', 'SES@admin2024', 'admin')
            if success:
                print("✓ Usuário admin padrão criado com sucesso")
            else:
                print(f"✗ Erro ao criar usuário admin: {message}")
                return False
        else:
            print("✓ Usuário admin já existe")

        print("✓ Banco de dados inicializado com sucesso!")
        return True

    except Exception as e:
        print(f"✗ Erro ao inicializar banco de dados: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)