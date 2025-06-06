import multiprocessing

# Gunicorn configuration for production

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gthread'
threads = 4
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'cinetrack'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None

# Server hooks
def on_starting(server):
    """Log that the server is starting."""
    server.log.info("Starting CineTrack server")

def on_exit(server):
    """Log that the server is stopping."""
    server.log.info("Stopping CineTrack server")

def worker_abort(worker):
    """Log worker crashes."""
    worker.log.info("Worker received SIGABRT signal") 