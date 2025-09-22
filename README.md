# Sistema de Gestão SES

Sistema de gestão de reservas de salas e equipamentos para a Secretaria Estadual de Saúde.

## Funcionalidades

- ✅ Sistema de autenticação com diferentes níveis de acesso (admin, cotead, colaborador)
- ✅ Agendamento de salas com verificação de conflitos
- ✅ Gestão de equipamentos com controle de estoque
- ✅ Dashboard administrativo com estatísticas
- ✅ Visualização de agenda em calendário
- ✅ Banco de dados SQLite com persistência

## Tecnologias

- **Backend:** Python Flask
- **Banco:** SQLite
- **Frontend:** HTML, CSS, JavaScript (Tailwind CSS, Flowbite)
- **Deploy:** Render

## Deploy no Render

### Configuração Automática

1. Conecte seu repositório no Render
2. O sistema detectará automaticamente os arquivos de configuração:
   - `render.yaml` - Configuração principal
   - `requirements.txt` - Dependências Python
   - `Procfile` - Comando de inicialização
   - `runtime.txt` - Versão do Python

### Variáveis de Ambiente

O sistema configura automaticamente:
- `SECRET_KEY` - Chave secreta gerada automaticamente
- `RENDER` - Flag para ambiente de produção
- `PORT` - Porta configurada dinamicamente

### Usuário Padrão

Após o deploy, o sistema criará automaticamente o usuário administrador:
- **Usuário:** admin@ses
- **Senha:** SES@admin2024

⚠️ **IMPORTANTE:** Altere a senha padrão após o primeiro login!

## Estrutura do Projeto

```
projeto-SES/
├── app.py              # Aplicação principal Flask
├── database.py         # Configuração e funções do banco
├── init_db.py         # Script de inicialização do banco
├── requirements.txt   # Dependências Python
├── render.yaml        # Configuração do Render
├── Procfile          # Comando de inicialização
├── runtime.txt       # Versão do Python
├── .gitignore        # Arquivos ignorados pelo Git
├── templates/        # Templates HTML
│   ├── index.html
│   ├── login.html
│   ├── admin_dashboard.html
│   ├── agenda.html
│   ├── agendar_sala.html
│   ├── equipamentos.html
│   └── ...
└── static/           # Arquivos estáticos
    └── sesgov.jpg
```

## Funcionalidades por Perfil

### Administrador (admin)
- Acesso completo ao sistema
- Gerenciamento de usuários
- Gerenciamento de equipamentos
- Visualização de todas as reservas
- Edição e exclusão de reservas

### Cotead/Colaborador
- Agendamento de salas
- Visualização da agenda
- Gerenciamento básico de equipamentos

## Banco de Dados

### Tabelas Principais

- **Users:** Usuários do sistema
- **Sala:** Salas disponíveis
- **Setor:** Setores da SES
- **Equipamentos:** Equipamentos disponíveis
- **Reservas:** Agendamentos realizados

### Backup e Persistência

- O banco SQLite é persistido no sistema de arquivos
- Em produção, fica localizado em `/opt/render/project/src/salas.db`
- Modo WAL habilitado para melhor concorrência

## Desenvolvimento Local

1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Execute: `python app.py`
4. Acesse: `http://localhost:5000`

## Segurança

- Senhas são hasheadas com Werkzeug
- Sessões seguras com chave secreta
- Verificação de permissões por rota
- Proteção contra SQL Injection
- Validação de entrada de dados

## Troubleshooting

### ❌ Erro 504 Bad Gateway (SOLUCIONADO)

Se você receber erro 504, as seguintes correções foram implementadas:

#### ✅ Soluções Aplicadas:
1. **Timeout aumentado** para 120 segundos
2. **Health check** configurado em `/health`
3. **Gunicorn otimizado** com configuração personalizada
4. **Inicialização de banco melhorada** com fallbacks
5. **Múltiplos caminhos** para persistência do banco
6. **Configurações de performance** do SQLite otimizadas

#### 🔧 Configurações Implementadas:
- Workers: 1 (ideal para plano free)
- Timeout: 120s
- Preload: Ativado
- Health check: `/health`
- Bind: 0.0.0.0:$PORT
- Journal mode: WAL
- Cache otimizado

#### 📊 Verificar Status:
- Acesse `/health` para verificar se o serviço está funcionando
- Logs disponíveis no dashboard do Render
- Backup automático dos dados implementado

#### 🚨 Em Caso de Problemas:
1. **Verifique os logs** no Render Dashboard
2. **Teste o health check**: `https://seu-app.onrender.com/health`
3. **Redeploy** se necessário
4. **Execute backup**: `python backup_data.py`

### 💾 Backup dos Dados

Para garantir que os dados nunca sejam perdidos:

```bash
# Fazer backup
python backup_data.py

# Verificar integridade
python -c "from backup_data import check_data_integrity; check_data_integrity()"

# Restaurar dados (se necessário)
python -c "from backup_data import restore_from_json; restore_from_json('backup_file.json')"
```

### 🔍 Monitoramento

- **Health Check**: `/health` retorna status do banco
- **Logs**: Disponíveis no Render Dashboard
- **Métricas**: Tempo de resposta e status HTTP

## Suporte

Para dúvidas ou problemas:
1. Verifique os logs no Render
2. Teste o endpoint `/health`
3. Execute script de backup
4. Entre em contato com a equipe de TI da SES
