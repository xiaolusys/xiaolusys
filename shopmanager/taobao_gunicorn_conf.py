#pidfile='/var/www/deploy/taobao/gunicorn.pid'
#daemon=True
import multiprocessing

workers=multiprocessing.cpu_count() * 2 + 1
bind="127.0.0.1:9000"

timeout=60
worker_connections=multiprocessing.cpu_count() * 500
max_requests=500
backlog=multiprocessing.cpu_count()*300

#accesslog='/var/log/taobao/gunicorn.out'
access_log_format="%(h)s %(l)s %(u)s %(t)s "

errorlog='/var/log/taobao/gunicorn.err'
loglevel='error'
  
