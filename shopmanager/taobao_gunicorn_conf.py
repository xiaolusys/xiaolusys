#pidfile='/home/user1/deploy/taobao/gunicorn.pid'
#daemon=True
workers=10
bind="127.0.0.1:9000"

timeout=300

accesslog='/home/user1/deploy/taobao/gunicorn.out'
access_log_format="%(h)s %(l)s %(u)s %(t)s "

errorlog='/home/user1/deploy/taobao/gunicorn.err'
loglevel='warning'
  
