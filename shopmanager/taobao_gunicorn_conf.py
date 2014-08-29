#pidfile='/var/www/deploy/taobao/gunicorn.pid'
#daemon=True
import multiprocessing

workers=multiprocessing.cpu_count() * 2 + 1
bind="127.0.0.1:9000"

timeout=10
worker_connections=500

accesslog='/var/www/deploy/taobao/gunicorn.out'
access_log_format="%(h)s %(l)s %(u)s %(t)s "

errorlog='/var/www/deploy/taobao/gunicorn.err'
loglevel='warning'
  
