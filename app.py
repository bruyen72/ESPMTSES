from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from functools import wraps
from database import conectar, criar_tabelas, adicionar_usuario, buscar_usuario, verificar_senha, buscar_todos_usuarios
from flask_login import current_user
import os


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key_for_development_only')

# Decorator para verificar permissões
def requer_cargo(cargos_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'cargo' not in session:
                flash('Faça login para acessar esta página.', 'error')
                return redirect(url_for('login'))
            if session['cargo'] not in cargos_permitidos:
                flash('Você não tem permissão para acessar esta página.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Garantir que as tabelas sejam criadas ao iniciar o aplicativo
criar_tabelas()

# Criar usuário admin padrão se não existir nenhum usuário
with app.app_context():
    if not buscar_usuario('admin@ses'):
        adicionar_usuario('admin@ses', 'SES@admin2024', 'admin')
        
        print('Usuário admin padrão criado.')
        
        

@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html', cargo=session.get('cargo'))
    return redirect(url_for('agenda'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = buscar_usuario(username)

        if user and verificar_senha(user, password):
            session['username'] = username
            session['cargo'] = user[3]  # cargo está na posição 3 da tupla
            session['user_id'] = user[0]  # Adicionar ID do usuário à sessão
            flash('Login efetuado com sucesso!', 'success')
            if user[3] in ('admin','cotead','colaborador') :
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('agenda'))
        else:
            flash('Login falhou. Verifique seu usuário e senha.', 'error')
            return render_template('login.html', username=username)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout efetuado com sucesso!', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@requer_cargo(['admin'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cargo = request.form['cargo']

        # Registros de usuários normais só podem ser cotead ou colaborador
        if cargo not in ['cotead', 'colaborador']:
            flash('Cargo inválido. Escolha cotead ou colaborador.', 'error')
            return render_template('register.html', username=username)

        if adicionar_usuario(username, password, cargo):
            flash('Usuário registrado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        flash('Registro falhou. Nome de usuário já existe.', 'error')
        return render_template('register.html', username=username)
    return render_template('register.html')

@app.route('/register', methods=['GET', 'POST'])
@requer_cargo(['admin'])
def register_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cargo = request.form['cargo']

        if adicionar_usuario(username, password, cargo):
            flash('Usuário registrado com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Registro falhou. Nome de usuário já existe.', 'error')
        return render_template('register_admin.html', username=username)
    return render_template('register_admin.html')



@app.route('/admin_dashboard')
@requer_cargo(['admin','cotead','colaborador'])
def admin_dashboard():
    conn = conectar()
    cursor = conn.cursor()

    try:
        # Buscar todas as reservas
        cursor.execute(''' 
            SELECT r.*, s.nome as sala_nome 
            FROM Reservas r 
            JOIN Sala s ON r.sala_id = s.id 
            ORDER BY r.data DESC
        ''')
        reservas = cursor.fetchall()

        # Buscar todos os usuários
        usuarios = buscar_todos_usuarios()

        # Buscar estatísticas de equipamentos
        cursor.execute('SELECT * FROM Equipamentos')
        equipamentos = cursor.fetchall()

        return render_template('admin_dashboard.html', 
                            reservas=reservas, 
                            usuarios=usuarios, 
                            equipamentos=equipamentos)
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        conn.close()

@app.route('/agendar', methods=['GET', 'POST'])
@requer_cargo(['admin', 'cotead', 'colaborador'])
def agendar_sala():
    if session.get('cargo') == '':
        flash('Apenas Usuários podem agendar salas.', 'info')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            nome = request.form['nome']
            matricula = request.form['matricula']
            setor_id = request.form['setor_id']
            sala_id = request.form['sala_id']
            data = request.form['data']
            periodo = request.form['periodo']
            equipamentos = request.form.getlist('equipamentos')

            usuario_logado = session.get('user_id')  #pegando usuario logado

            conn = conectar()
            cursor = conn.cursor()

            # Verificar conflitos
            cursor.execute('SELECT periodo FROM Reservas WHERE sala_id = ? AND data = ?', (sala_id, data))
            reservas_existentes = cursor.fetchall()

            conflito = False
            for reserva in reservas_existentes:
                periodo_existente = reserva[0]
                if periodo == "integral" or periodo_existente == "integral":
                    conflito = True
                elif (periodo == "matutino" and periodo_existente == "vespertino") or (periodo == "vespertino" and periodo_existente == "matutino"):
                    conflito = False
                else:
                    conflito = True

            if conflito:
                flash('Esta sala já está reservada para este período.', 'error')
                return redirect(url_for('agendar_sala'))

            cursor.execute('BEGIN TRANSACTION')

            # Atualizar equipamentos
            for equipamento in equipamentos:
                cursor.execute('''
                    UPDATE Equipamentos 
                    SET quantidade = quantidade - 1 
                    WHERE nome = ? AND quantidade > 0
                ''', (equipamento,))

            # Inserir reserva
            cursor.execute('''
                INSERT INTO Reservas (nome, matricula, setor_id, sala_id, data, periodo, equipamentos,user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nome, matricula, setor_id, sala_id, data, periodo, ', '.join(equipamentos),usuario_logado))

            cursor.execute('COMMIT')
            flash('Reserva efetuada com sucesso!', 'success')
            
        except Exception as e:
            if 'cursor' in locals():
                cursor.execute('ROLLBACK')
            flash(f'Erro ao realizar reserva: {str(e)}', 'error')
        finally:
            if 'conn' in locals():
                conn.close()

        return redirect(url_for('agenda'))

    # Carregar dados para o formulário
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Equipamentos WHERE quantidade > 0')
        equipamentos = cursor.fetchall()
        
        cursor.execute('SELECT * FROM Sala')
        salas = cursor.fetchall()
        
        return render_template('agendar_sala.html', 
                             equipamentos=equipamentos,
                             salas=salas)
    except Exception as e:
        flash(f'Erro ao carregar dados: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/agenda')
@requer_cargo(['admin', 'cotead', 'colaborador'])
def agenda():
    return render_template('agenda.html')

# Substitua a função get_reservas com esta versão corrigida
@app.route('/get_reservas')
@requer_cargo(['admin', 'cotead', 'colaborador'])
def get_reservas():
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.id, r.nome, r.data, r.periodo, s.nome as sala_nome, se.nome as setor_id, r.matricula, u.username
            FROM Reservas r
            JOIN Sala s ON r.sala_id = s.id
            JOIN Setor se ON r.setor_id = se.id
            JOIN Users u ON r.user_id = u.id                         
        ''')
        reservas = cursor.fetchall()
        
        eventos = []
        for reserva in reservas:
            data = reserva[2]
            periodo = reserva[3]

            if periodo == 'matutino':
                start_time = '08:00'
                end_time = '12:00'
            elif periodo == 'vespertino':
                start_time = '13:00'
                end_time = '17:00'
            else:  # integral
                start_time = '08:00'
                end_time = '17:00'

            eventos.append({
                'id': reserva[0],
                'title': reserva[1] + ' - ' + reserva[4] + ' - ' + reserva[5],
                'start': f"{data}T{start_time}",
                'end': f"{data}T{end_time}",
                'extendedProps': {
                    'sala': reserva[4],
                    'setor': reserva[5],
                    'matricula': reserva[6],
                    'usuario_logado': reserva[7]
                }
            })

        return jsonify(eventos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/equipamentos', methods=['GET', 'POST'])
@requer_cargo(['admin'])

def equipamentos():
     
    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome_equip = request.form['nome']
        quantidade = request.form['quantidade']

        try:
            cursor.execute('INSERT INTO Equipamentos (nome, quantidade) VALUES (?, ?)', 
                         (nome_equip, quantidade))
            conn.commit()
            flash('Equipamento cadastrado com sucesso!', 'success')
        except Exception as e:
            print(f"Erro ao cadastrar equipamento: {e}")
            flash('Erro ao cadastrar equipamento.', 'error')
        finally:
            conn.close()

        return redirect(url_for('equipamentos'))

    cursor.execute('SELECT * FROM Equipamentos')
    equipamentos = cursor.fetchall()
    conn.close()

    return render_template('equipamentos.html', equipamentos=equipamentos)

@app.route('/deletar/<int:id>')
@requer_cargo(['admin'])
def deletar_reserva(id):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute('BEGIN TRANSACTION')
        
        # Primeiro, recuperar os equipamentos da reserva
        cursor.execute('SELECT equipamentos FROM Reservas WHERE id = ?', (id,))
        reserva = cursor.fetchone()
        if reserva and reserva[0]:
            equipamentos = reserva[0].split(', ')
            # Devolver os equipamentos ao estoque
            for equipamento in equipamentos:
                cursor.execute('UPDATE Equipamentos SET quantidade = quantidade + 1 WHERE nome = ?', 
                             (equipamento,))
        
        cursor.execute('DELETE FROM Reservas WHERE id = ?', (id,))
        cursor.execute('COMMIT')
        flash('Reserva excluída com sucesso!', 'success')
    except Exception as e:
        cursor.execute('ROLLBACK')
        print(f"Erro ao deletar reserva: {e}")
        flash('Erro ao excluir reserva.', 'error')
    finally:
        conn.close()

    return redirect(url_for('admin_dashboard'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@requer_cargo(['admin'])
def editar_reserva(id):
    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        matricula = request.form['matricula']
        setor_id = request.form['setor_id']
        sala_id = request.form['sala_id']
        data = request.form['data']
        periodo = request.form['periodo']
        equipamentos = request.form.getlist('equipamentos')

        try:
            cursor.execute('BEGIN TRANSACTION')
            
            # Primeiro, recuperar os equipamentos antigos da reserva
            cursor.execute('SELECT equipamentos FROM Reservas WHERE id = ?', (id,))
            reserva_antiga = cursor.fetchone()
            if reserva_antiga and reserva_antiga[0]:
                equipamentos_antigos = reserva_antiga[0].split(', ')
                # Devolver os equipamentos antigos ao estoque
                for equipamento in equipamentos_antigos:
                    cursor.execute('UPDATE Equipamentos SET quantidade = quantidade + 1 WHERE nome = ?', 
                                 (equipamento,))

            # Atualizar a reserva com os novos dados
            cursor.execute('''UPDATE Reservas
                          SET nome = ?, matricula = ?, setor_id = ?, sala_id = ?, 
                              data = ?, periodo = ?, equipamentos = ?
                          WHERE id = ?''', 
                          (nome, matricula, setor_id, sala_id, data, periodo, 
                           ', '.join(equipamentos), id))

            # Atualizar o estoque com os novos equipamentos
            for equipamento in equipamentos:
                cursor.execute('UPDATE Equipamentos SET quantidade = quantidade - 1 WHERE nome = ?', 
                             (equipamento,))

            cursor.execute('COMMIT')
            flash('Reserva atualizada com sucesso!', 'success')
        except Exception as e:
            cursor.execute('ROLLBACK')
            print(f"Erro ao atualizar reserva: {e}")
            flash('Erro ao atualizar reserva.', 'error')
        finally:
            conn.close()

        return redirect(url_for('admin_dashboard'))

    # Carregar dados da reserva para edição
    cursor.execute('SELECT * FROM Reservas WHERE id = ?', (id,))
    reserva = cursor.fetchone()
    
    cursor.execute('SELECT * FROM Equipamentos')
    equipamentos = cursor.fetchall()
    
    conn.close()

    return render_template('editar_reserva.html', reserva=reserva, equipamentos=equipamentos)

@app.route('/deletar_equipamento/<int:id>')
@requer_cargo(['admin','cotead','colaborador'])
def deletar_equipamento(id):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute('BEGIN TRANSACTION')
        cursor.execute('DELETE FROM Equipamentos WHERE id = ?', (id,))
        cursor.execute('COMMIT')
        flash('Equipamento excluído com sucesso!', 'success')
    except Exception as e:
        cursor.execute('ROLLBACK')
        print(f"Erro ao deletar equipamento: {e}")
        flash('Erro ao excluir equipamento.', 'error')
    finally:
        conn.close()

    return redirect(url_for('equipamentos'))

@app.route('/editar_equipamento/<int:id>', methods=['GET', 'POST'])
@requer_cargo(['admin'])
def editar_equipamento(id):
    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        quantidade = request.form['quantidade']

        try:
            cursor.execute('BEGIN TRANSACTION')
            cursor.execute('UPDATE Equipamentos SET nome = ?, quantidade = ? WHERE id = ?',
                    (nome, quantidade, id))
            cursor.execute('COMMIT')
            flash('Equipamento atualizado com sucesso!', 'success')
        except Exception as e:
            cursor.execute('ROLLBACK')
            print(f"Erro ao atualizar equipamento: {e}")
            flash('Erro ao atualizar equipamento.', 'error')
        finally:
            conn.close()

        return redirect(url_for('equipamentos'))

    cursor.execute('SELECT * FROM Equipamentos WHERE id = ?', (id,))
    equipamento = cursor.fetchone()
    conn.close()

    return render_template('editar_equipamento.html', equipamento=equipamento)

@app.route('/usuarios')
@requer_cargo(['admin'])
def usuarios():
    try:
        usuarios = buscar_todos_usuarios()
        return render_template('usuarios.html', usuarios=usuarios)
    except Exception as e:
        flash(f'Erro ao carregar usuários: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/deletar_usuario/<int:id>')
@requer_cargo(['admin'])
def deletar_usuario(id):
    # Verificar se está tentando excluir a si mesmo
    if id == session.get('user_id'):
        flash('Não é possível excluir seu próprio usuário.', 'error')
        return redirect(url_for('usuarios'))

    conn = conectar()
    cursor = conn.cursor()
    try:
        # Iniciar transação
        cursor.execute('BEGIN TRANSACTION')
        
        # Buscar informações do usuário
        cursor.execute('SELECT username, cargo FROM Users WHERE id = ?', (id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.execute('ROLLBACK')
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('usuarios'))
        
        username, cargo = user
        
        # Verificar se é o admin padrão
        if username == 'admin@ses':
            cursor.execute('ROLLBACK')
            flash('Não é possível excluir o usuário admin padrão.', 'error')
            return redirect(url_for('usuarios'))
        
        # Contar número de admins
        cursor.execute('SELECT COUNT(*) FROM Users WHERE cargo = "admin"')
        admin_count = cursor.fetchone()[0]
        
        # Impedir exclusão do último admin
        if cargo == 'admin' and admin_count <= 1:
            cursor.execute('ROLLBACK')
            flash('Não é possível excluir o último administrador.', 'error')
            return redirect(url_for('usuarios'))
        
        # Remover reservas do usuário
        cursor.execute('DELETE FROM Reservas WHERE nome = ? OR matricula = ?', (username, username))
        
        # Deletar usuário
        cursor.execute('DELETE FROM Users WHERE id = ?', (id,))
        
        # Registrar log de auditoria
        cursor.execute('''
            INSERT INTO AuditLog (admin_username, action, target_username, target_cargo, timestamp) 
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', (session.get('username', 'Sistema'), 'delete_user', username, cargo))
        
        # Confirmar transação
        cursor.execute('COMMIT')
        flash(f'Usuário {username} excluído com sucesso!', 'success')
        
    except Exception as e:
        cursor.execute('ROLLBACK')
        print(f"Erro ao excluir usuário: {e}")
        flash('Erro ao excluir usuário.', 'error')
    finally:
        conn.close()

    return redirect(url_for('usuarios'))

@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
@requer_cargo(['admin'])
def editar_usuario(id):
    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        try:
            cursor.execute('BEGIN TRANSACTION')
            
            nome = request.form['username']
            cargo = request.form['cargo']

            # Não permitir alterar cargo de admin
            cursor.execute('SELECT cargo FROM Users WHERE id = ?', (id,))
            user = cursor.fetchone()
            if user and user[0] == 'admin' and cargo != 'admin':
                cursor.execute('ROLLBACK')
                flash('Não é possível alterar o cargo de um administrador.', 'error')
                return redirect(url_for('usuarios'))

            cursor.execute('UPDATE Users SET username = ?, cargo = ? WHERE id = ?',
                    (nome, cargo, id))
            
            cursor.execute('COMMIT')
            flash('Usuário atualizado com sucesso!', 'success')
            
        except Exception as e:
            cursor.execute('ROLLBACK')
            print(f"Erro ao atualizar usuário: {e}")
            flash('Erro ao atualizar usuário.', 'error')
        finally:
            conn.close()

        return redirect(url_for('usuarios'))

    cursor.execute('SELECT * FROM Users WHERE id = ?', (id,))
    usuario = cursor.fetchone()
    conn.close()

    return render_template('editar_usuario.html', usuario=usuario)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)