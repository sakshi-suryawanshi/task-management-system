"""
Gunicorn configuration file for Task Management System.

This configuration file provides production-ready settings for running Django
application with Gunicorn WSGI HTTP Server.

For more information about Gunicorn configuration, see:
https://docs.gunicorn.org/en/stable/settings.html

Usage:
    gunicorn taskmanager.wsgi:application -c gunicorn_config.py

Or via environment variables:
    gunicorn taskmanager.wsgi:application --config gunicorn_config.py
"""

import os
import multiprocessing
import logging.config

# ============================================================================
# Server Socket Configuration
# ============================================================================

# The socket to bind to (IP:PORT or unix socket path)
# Default: '127.0.0.1:8000' - Changed to '0.0.0.0:8000' for Docker
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')

# The number of pending connections (backlog)
# This is the maximum number of pending connections to the server
backlog = int(os.environ.get('GUNICORN_BACKLOG', '2048'))

# ============================================================================
# Worker Process Configuration
# ============================================================================

# The number of worker processes for handling requests
# Recommended: (2 x CPU cores) + 1 for production
# For local development, using 3 workers is reasonable
# Can be overridden via GUNICORN_WORKERS environment variable
# Default: 3 (suitable for local development)
cpu_count = multiprocessing.cpu_count()
workers = int(os.environ.get('GUNICORN_WORKERS', min(3, (cpu_count * 2) + 1)))

# The type of worker class to use
# 'sync' is the default and most stable for Django
# Alternatives: 'gevent', 'eventlet', 'tornado' (require additional packages)
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'sync')

# The number of worker threads per process
# Only used with 'gthread' worker class
# For sync workers, this is ignored
# For better concurrency with sync workers, increase worker count instead
worker_connections = int(os.environ.get('GUNICORN_WORKER_CONNECTIONS', '1000'))

# Threads per worker process (only for gthread worker class)
# When using gthread worker class, this allows each worker to handle multiple requests
# For sync workers, this is ignored (use more workers instead)
# Can be overridden via GUNICORN_THREADS environment variable
# Default: 1 (sync workers don't use threads)
threads = int(os.environ.get('GUNICORN_THREADS', '1'))

# Maximum number of requests a worker will process before restarting
# This helps prevent memory leaks by recycling worker processes
# Set to 0 to disable
max_requests = int(os.environ.get('GUNICORN_MAX_REQUESTS', '1000'))

# Maximum number of requests a worker will process before restarting (with jitter)
# Adds randomization to max_requests to prevent all workers from restarting simultaneously
# Recommended: 0.1 * max_requests (10% jitter)
max_requests_jitter = int(os.environ.get('GUNICORN_MAX_REQUESTS_JITTER', '100'))

# Timeout for graceful workers restart (in seconds)
# Workers will be killed and restarted after this timeout if they haven't finished
# This prevents workers from hanging indefinitely
timeout = int(os.environ.get('GUNICORN_TIMEOUT', '120'))

# Graceful timeout for worker restart (in seconds)
# Workers have this much time to finish processing requests before being killed
graceful_timeout = int(os.environ.get('GUNICORN_GRACEFUL_TIMEOUT', '30'))

# Keep alive timeout (in seconds)
# How long to wait for requests on a Keep-Alive connection
keepalive = int(os.environ.get('GUNICORN_KEEPALIVE', '2'))

# ============================================================================
# Logging Configuration
# ============================================================================

# Access log file path
# Use '-' to log to stdout (recommended for Docker)
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', '-')

# Error log file path
# Use '-' to log to stderr (recommended for Docker)
errorlog = os.environ.get('GUNICORN_ERROR_LOG', '-')

# The granularity of log output
# Options: 'debug', 'info', 'warning', 'error', 'critical'
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info').lower()

# Format for access log
# Custom format with request timing and response codes
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" '
    '%(D)s %(p)s'
)
# Format explanation:
# %(h)s - remote address (IP)
# %(l)s - remote logname (usually '-')
# %(u)s - remote user (if authenticated)
# %(t)s - request timestamp
# %(r)s - request line (method, path, HTTP version)
# %(s)s - HTTP status code
# %(b)s - response length (bytes)
# %(f)s - referrer
# %(a)s - user agent
# %(D)s - request duration in microseconds
# %(p)s - process ID

# ============================================================================
# Process Naming Configuration
# ============================================================================

# A base to use with setproctitle for process naming
# This helps identify Gunicorn processes in system monitoring
proc_name = os.environ.get('GUNICORN_PROC_NAME', 'taskmanager')

# ============================================================================
# Server Mechanics Configuration
# ============================================================================

# Daemonize the Gunicorn process (detach & enter background)
# Set to False for Docker (Docker handles process management)
daemon = False

# The PID file location (only when daemonizing)
pidfile = os.environ.get('GUNICORN_PIDFILE', None)

# User to run worker processes as
# For security, should run as non-root user (handled in Dockerfile)
user = os.environ.get('GUNICORN_USER', None)

# Group to run worker processes as
group = os.environ.get('GUNICORN_GROUP', None)

# Temporary directory for request data
tmp_upload_dir = os.environ.get('GUNICORN_TMP_UPLOAD_DIR', None)

# ============================================================================
# SSL/TLS Configuration (for production with HTTPS)
# ============================================================================

# Keyfile path for SSL (if using HTTPS)
keyfile = os.environ.get('GUNICORN_KEYFILE', None)

# Certfile path for SSL (if using HTTPS)
certfile = os.environ.get('GUNICORN_CERTFILE', None)

# ============================================================================
# Performance Tuning Configuration
# ============================================================================

# Enable SO_REUSEPORT option on the listening socket
# Allows multiple processes to bind to the same port (Linux 3.9+)
# This can improve performance by better distributing connections
reuse_port = os.environ.get('GUNICORN_REUSE_PORT', 'False').lower() == 'true'

# Limit the size of HTTP request headers
# Prevents memory exhaustion from large headers
limit_request_line = int(os.environ.get('GUNICORN_LIMIT_REQUEST_LINE', '4094'))

# Limit the number of HTTP header fields in a request
# Prevents memory exhaustion from too many headers
limit_request_fields = int(os.environ.get('GUNICORN_LIMIT_REQUEST_FIELDS', '100'))

# Limit the size of HTTP request header field
# Prevents memory exhaustion from large header values
limit_request_field_size = int(os.environ.get('GUNICORN_LIMIT_REQUEST_FIELD_SIZE', '8190'))

# ============================================================================
# Pre/Post Fork Hooks (Optional)
# ============================================================================

def on_starting(server):
    """
    Called just before the master process is initialized.
    Useful for logging startup information.
    """
    server.log.info("Starting Gunicorn server for Task Management System")


def on_reload(server):
    """
    Called to recycle workers during a reload via SIGHUP.
    """
    server.log.info("Reloading Gunicorn workers...")


def when_ready(server):
    """
    Called just after the server is started.
    """
    server.log.info(f"Gunicorn server is ready. Listening on: {bind}")
    server.log.info(f"Server process ID: {os.getpid()}")
    server.log.info(f"Workers: {workers}")


def worker_int(worker):
    """
    Called when a worker receives INT or QUIT signal.
    """
    worker.log.info("Worker received INT or QUIT signal")


def pre_fork(server, worker):
    """
    Called just before a worker is forked.
    """
    pass


def post_fork(server, worker):
    """
    Called just after a worker has been forked.
    """
    server.log.info(f"Worker spawned (pid: {worker.pid})")


def post_worker_init(worker):
    """
    Called just after a worker has initialized the application.
    """
    worker.log.info("Worker initialized")


def worker_abort(worker):
    """
    Called when a worker receives the SIGABRT signal.
    """
    worker.log.info("Worker received ABRT signal")


def pre_exec(server):
    """
    Called just before a new master process is forked.
    """
    server.log.info("Forking new master process")


def worker_exit(server, worker):
    """
    Called just after a worker has been exited, in the master process.
    """
    server.log.info(f"Worker exited (pid: {worker.pid})")


def nworkers_changed(server, new_value, old_value):
    """
    Called just after num_workers has been changed.
    """
    server.log.info(f"Worker count changed from {old_value} to {new_value}")


# ============================================================================
# Logging Configuration for Gunicorn
# ============================================================================

# Configure Python logging for Gunicorn
# This ensures consistent log formatting
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {process:d} {thread:d} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'stream': 'ext://sys.stderr',
        },
    },
    'root': {
        'level': loglevel.upper(),
        'handlers': ['console'],
    },
    'loggers': {
        'gunicorn.error': {
            'level': loglevel.upper(),
            'handlers': ['console'],
            'propagate': False,
        },
        'gunicorn.access': {
            'level': loglevel.upper(),
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

# Apply logging configuration
logging.config.dictConfig(LOGGING_CONFIG)

