pidfile = '/tmp/gunicorn.pid'
daemon = True
workers = 6
bind = "127.0.0.1:9000"

accesslog = '/tmp/gunicorn.out'
access_log_format = "%(h)s %(l)s %(u)s %(t)s "

errorlog = '/tmp/gunicorn.err'
loglevel = 'warning'
