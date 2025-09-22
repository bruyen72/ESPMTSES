import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Configuração do banco de dados para produção
def get_database_path():
    if os.environ.get('RENDER'):
        # Tentar diferentes caminhos possíveis no Render
        possible_paths = [
            '/opt/render/project/src/salas.db',
            '/tmp/salas.db',
            './salas.db',
            'salas.db'
        ]

        for path in possible_paths:
            try:
                # Criar diretório se necessário
                dir_path = os.path.dirname(path)
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)

                # Testar se podemos escrever no local
                test_conn = sqlite3.connect(path)
                test_conn.close()
                return path
            except:
                continue

        # Fallback para diretório atual
        return 'salas.db'
    else:
        return 'salas.db'

DATABASE = get_database_path()

def conectar():
    try:
        conn = sqlite3.connect(DATABASE, timeout=30.0)
        conn.execute('PRAGMA foreign_keys = ON')
        conn.execute('PRAGMA journal_mode = WAL')  # Melhor para concorrência
        conn.execute('PRAGMA synchronous = NORMAL')  # Melhor performance
        conn.execute('PRAGMA cache_size = 10000')  # Cache maior
        conn.execute('PRAGMA temp_store = MEMORY')  # Usar memória para temp
        return conn
    except Exception as e:
        print(f"Erro ao conectar com banco: {e}")
        # Fallback para memória em caso de erro crítico
        conn = sqlite3.connect(':memory:')
        return conn

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()


   # Criação das tabelas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Sala (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            capacidade INTEGER NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Setor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Equipamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            cargo TEXT NOT NULL CHECK(cargo IN ('admin', 'cotead', 'colaborador')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            active BOOLEAN DEFAULT 1
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            matricula TEXT NOT NULL,
            setor_id INTEGER NOT NULL,
            sala_id INTEGER NOT NULL,
            data DATE NOT NULL,
            periodo TEXT NOT NULL CHECK(periodo IN ('matutino', 'vespertino', 'integral')),
            equipamentos TEXT,
            user_id INTERGER NOT NULL,
            FOREIGN KEY (sala_id) REFERENCES Sala(id) ON DELETE CASCADE,
            FOREIGN KEY (setor_id) REFERENCES Setor(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
        )
    ''')

    # Inserção de dados iniciais em Sala
    cursor.execute('SELECT COUNT(*) FROM Sala')
    if cursor.fetchone()[0] == 0:
        salas = [
            ('Sala 1', 40),
            ('Sala 2', 40),
            ('Sala 3', 40),
            ('Sala 4', 40),
            ('Sala 5', 40),
            ('Sala 6', 40),
            ('Sala 7', 40),
            ('Sala 8', 40),
            ('Auditório', 150)
        ]
        cursor.executemany('INSERT INTO Sala (nome, capacidade) VALUES (?, ?)', salas)

    # Inserção de dados iniciais em Setor
    cursor.execute('SELECT COUNT(*) FROM Setor')
    if cursor.fetchone()[0] == 0:
        setor = [
            ('Coepe', 'coepe@ses.mt.gov.br', '3613-5342'),
            ('Cogepe', 'cogepe@ses.mt.gov.br', '3613-5346'),
            ('Coftes', 'coftes@ses.mt.gov.br', '3613-5330'),
            ('Coades', 'coades@ses.mt.gov.br', '3613-5325'),
            ('Cotead', 'cotead@ses.mt.gov.br', '3613-5340'),
            ('Gaesp', 'gaesp@ses.mt.gov.br', '3613-5327'),
            ('Gdr', 'gdr@ses.mt.gov.br', '3613-5324'),
            ('Cies', 'ciesmt@ses.mt.gov.br', '-'),
            ('Comitê de Ética', 'cep@ses.mt.gov.br', '3613-5351'),
            ('Núcleo de Residência em Saúde', 'nucleoderesidenciaemsaude@ses.mt.gov.br', '3613-5919'),
            ('Outros', '-', '-')
        ]
        cursor.executemany('INSERT INTO Setor (nome, email, telefone) VALUES (?, ?, ?)', setor)

    conn.commit()
    conn.close()

def adicionar_usuario(username, password, cargo):
    if cargo not in ['admin', 'cotead', 'colaborador']:
        return False, "Cargo inválido"
        
    conn = conectar()
    cursor = conn.cursor()
    try:
        password_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO Users (username, password_hash, cargo, created_at) 
            VALUES (?, ?, ?, datetime('now'))
        ''', (username, password_hash, cargo))
        conn.commit()
        return True, "Usuário criado com sucesso"
    except sqlite3.IntegrityError:
        return False, "Nome de usuário já existe"
    except Exception as e:
        return False, f"Erro ao criar usuário: {str(e)}"
    finally:
        conn.close()

def buscar_usuario(username):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT id, username, password_hash, cargo, created_at, last_login, active 
            FROM Users 
            WHERE username = ? AND active = 1
        ''', (username,))
        return cursor.fetchone()
    finally:
        conn.close()

def verificar_senha(user, password):
    if not user or not user[2]:
        return False
    return check_password_hash(user[2], password)

def buscar_todos_usuarios():
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT u.*, COUNT(r.id) as num_reservas 
            FROM Users u 
            LEFT JOIN Reservas r ON u.username = r.nome 
            WHERE u.active = 1 
            GROUP BY u.id 
            ORDER BY u.username
        ''')
        return cursor.fetchall()
    finally:
        conn.close()

def deletar_usuario(id, admin_username):
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Verificar se usuário existe e está ativo
        cursor.execute('SELECT username, cargo, active FROM Users WHERE id = ?', (id,))
        user = cursor.fetchone()
        
        if not user:
            return False, "Usuário não encontrado"
            
        if not user[2]:  # active = False
            return False, "Usuário já está inativo"
            
        username, cargo = user[0], user[1]
        
        # Verificar se é o admin padrão
        if username == 'admin@ses':
            return False, "Não é possível excluir o usuário admin padrão"
        
        # Verificar se é o último admin
        if cargo == 'admin':
            cursor.execute('SELECT COUNT(*) FROM Users WHERE cargo = "admin" AND active = 1')
            if cursor.fetchone()[0] <= 1:
                return False, "Não é possível excluir o último administrador"
        
        cursor.execute('BEGIN TRANSACTION')
        
        # Soft delete do usuário
        deleted_username = f"{username}_deleted_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cursor.execute('UPDATE Users SET active = 0, username = ? WHERE id = ?', 
                      (deleted_username, id))
        
        # Remover reservas
        cursor.execute('DELETE FROM Reservas WHERE nome = ? OR matricula = ?', 
                      (username, username))
        
        # Registrar na auditoria
        cursor.execute('''
            INSERT INTO AuditLog (admin_username, action, target_username, target_cargo, details) 
            VALUES (?, ?, ?, ?, ?)
        ''', (
            admin_username,
            'delete_user',
            username,
            cargo,
            f"Deleted by {admin_username} at {datetime.now()}"
        ))
        
        cursor.execute('COMMIT')
        return True, f"Usuário {username} excluído com sucesso"
        
    except Exception as e:
        cursor.execute('ROLLBACK')
        return False, f"Erro ao excluir usuário: {str(e)}"
    finally:
        conn.close()

def atualizar_usuario(id, novo_username=None, novo_cargo=None, admin_username=None):
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Verificar se usuário existe e está ativo
        cursor.execute('SELECT username, cargo, active FROM Users WHERE id = ?', (id,))
        user = cursor.fetchone()
        
        if not user:
            return False, "Usuário não encontrado"
            
        if not user[2]:  # active = False
            return False, "Usuário está inativo"
            
        username, cargo = user[0], user[1]
        
        # Verificar alterações no admin padrão
        if username == 'admin@ses' and novo_cargo and novo_cargo != 'admin':
            return False, "Não é possível alterar o cargo do admin padrão"
        
        # Verificar alteração do último admin
        if cargo == 'admin' and novo_cargo and novo_cargo != 'admin':
            cursor.execute('SELECT COUNT(*) FROM Users WHERE cargo = "admin" AND active = 1')
            if cursor.fetchone()[0] <= 1:
                return False, "Não é possível alterar o cargo do último administrador"
        
        cursor.execute('BEGIN TRANSACTION')
        
        updates = []
        params = []
        
        if novo_username:
            updates.append('username = ?')
            params.append(novo_username)
        
        if novo_cargo:
            if novo_cargo not in ['admin', 'cotead', 'colaborador']:
                return False, "Cargo inválido"
            updates.append('cargo = ?')
            params.append(novo_cargo)
        
        if updates:
            params.append(id)
            cursor.execute(f'''
                UPDATE Users 
                SET {', '.join(updates)}
                WHERE id = ?
            ''', params)
            
            # Registrar na auditoria
            cursor.execute('''
                INSERT INTO AuditLog (
                    admin_username, action, target_username, 
                    target_cargo, details
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                admin_username,
                'update_user',
                username,
                cargo,
                f"Updated by {admin_username}: {', '.join(updates)}"
            ))
        
        cursor.execute('COMMIT')
        return True, "Usuário atualizado com sucesso"
        
    except sqlite3.IntegrityError:
        cursor.execute('ROLLBACK')
        return False, "Nome de usuário já existe"
    except Exception as e:
        cursor.execute('ROLLBACK')
        return False, f"Erro ao atualizar usuário: {str(e)}"
    finally:
        conn.close()

def registrar_login(username):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE Users 
            SET last_login = datetime('now') 
            WHERE username = ?
        ''', (username,))
        conn.commit()
    finally:
        conn.close()

if __name__ == '__main__':
    criar_tabelas()
    print("Banco de dados inicializado com sucesso.")