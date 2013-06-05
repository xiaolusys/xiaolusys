#pidfile='/home/meixqhi/deploy/taobao/gunicorn.pid'
#daemon=True
workers=8
bind="127.0.0.1:9000"

accesslog='/home/meixqhi/deploy/taobao/gunicorn.out'
access_log_format="%(h)s %(l)s %(u)s %(t)s "

errorlog='/home/meixqhi/deploy/taobao/gunicorn.err'
loglevel='warning'
  
