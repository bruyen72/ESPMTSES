from flask import Flask, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <html>
        <head>
            <title>Lista de Reservas</title>
        </head>
        <body>
            <h1>Reservas</h1>
            <table border="1">
                <tr>
                    <th>Nome</th>
                    <th>Data</th>
                    <th>Período</th>
                    <th>Sala</th>
                    <th>Equipamentos</th>
                    <th>Ações</th>
                </tr>
                <!-- Aqui estariam as reservas recuperadas do banco de dados -->
                <!-- Simulação de uma linha de reserva -->
                <tr>
                    <td>João da Silva</td>
                    <td>2024-09-18</td>
                    <td>Matutino</td>
                    <td>Sala 101</td>
                    <td>Projetor, Notebook</td>
                    <td>
                        <a href="/deletar/1">Deletar</a>
                    </td>
                </tr>
            </table>
            <br>
            <a href="/form_reserva">Fazer uma nova reserva</a>
        </body>
    </html>
    '''

@app.route('/form_reserva')
def form_reserva():
    return '''
    <html>
        <head>
            <title>Formulário de Reserva</title>
        </head>
        <body>
            <h1>Fazer Reserva</h1>
            <form action="/reservar" method="POST">
                <label for="nome">Nome:</label><br>
                <input type="text" id="nome" name="nome" required><br><br>

                <label for="matricula">Matrícula:</label><br>
                <input type="text" id="matricula" name="matricula" required><br><br>

                <label for="setor">Setor:</label><br>
                <input type="text" id="setor" name="setor" required><br><br>

                <label for="sala_id">Sala:</label><br>
                <select id="sala_id" name="sala_id" required>
                    <option value="1">Sala 101</option>
                    <option value="2">Sala 102</option>
                    <!-- Outras opções de sala aqui -->
                </select><br><br>

                <label for="data">Data:</label><br>
                <input type="date" id="data" name="data" required><br><br>

                <label for="periodo">Período:</label><br>
                <select id="periodo" name="periodo" required>
                    <option value="matutino">Matutino</option>
                    <option value="vespertino">Vespertino</option>
                    <option value="integral">Integral</option>
                </select><br><br>

                <label for="equipamentos">Equipamentos:</label><br>
                <input type="checkbox" name="equipamentos" value="Projetor"> Projetor<br>
                <input type="checkbox" name="equipamentos" value="Notebook"> Notebook<br><br>

                <input type="submit" value="Reservar">
            </form>
        </body>
    </html>
    '''

@app.route('/reservar', methods=['POST'])
def reservar():
    nome = request.form['nome']
    matricula = request.form['matricula']
    setor = request.form['setor']
    sala_id = request.form['sala_id']
    data = request.form['data']
    periodo = request.form['periodo']
    equipamentos = ', '.join(request.form.getlist('equipamentos')) if request.form.getlist('equipamentos') else ''
    
    # Aqui você faria a lógica de inserção no banco de dados

    # Simulação de sucesso:
    return '''
    <html>
        <head>
            <title>Reserva Concluída</title>
        </head>
        <body>
            <h1>Reserva realizada com sucesso!</h1>
            <p>Nome: {}</p>
            <p>Data: {}</p>
            <p>Período: {}</p>
            <p>Sala: {}</p>
            <p>Equipamentos: {}</p>
            <a href="/">Voltar à lista de reservas</a>
        </body>
    </html>
    '''.format(nome, data, periodo, sala_id, equipamentos)

@app.route('/deletar/<int:id>')
def deletar_reserva(id):
    # Aqui você faria a lógica para deletar do banco de dados
    return '''
    <html>
        <head>
            <title>Reserva Deletada</title>
        </head>
        <body>
            <h1>Reserva deletada com sucesso!</h1>
            <a href="/">Voltar à lista de reservas</a>
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True)
