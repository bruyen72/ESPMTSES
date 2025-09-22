# Configuração do Gunicorn para Render
import os

# Configurações de servidor
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
workers = 1  # Para plano free do Render
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# Configurações de log
loglevel = "info"
accesslog = "-"
errorlog = "-"

# Configurações de inicialização
preload_app = True
daemon = False

# Configurações de performance
worker_tmp_dir = "/dev/shm"

# Função executada quando o master inicia
def on_starting(server):
    server.log.info("Servidor Gunicorn iniciando...")

# Função executada quando um worker é criado
def when_ready(server):
    server.log.info("Servidor pronto para receber conexões")

# Função executada quando um worker falha
def worker_abort(worker):
    worker.log.info("Worker abortado")

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    pass

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

    # get traceback info
    import threading
    import sys
    import traceback
    id2name = {th.ident: th.name for th in threading.enumerate()}
    code = []
    for thread_id, frame in sys._current_frames().items():
        code.append("\n# Thread: %s(%d)" % (id2name.get(thread_id,""), thread_id))
        for filename, lineno, name, line in traceback.extract_stack(frame):
            code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
            if line:
                code.append("  %s" % (line.strip()))
    worker.log.debug("\n".join(code))