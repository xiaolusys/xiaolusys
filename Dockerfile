from registry.aliyuncs.com/xiaolu-img/xiaolusys-base:d1ef28abab8678e42c332c05bbaf0a910bdf71f6

run mkdir -p /var/log/taobao;mkdir -p /var/www/deploy/taobao
add . /var/www/deploy/taobao/taobao-backend
run cp /var/www/deploy/taobao/taobao-backend/prod_settings.py.bk /var/www/deploy/taobao/taobao-backend/shopmanager/prod_settings.py
run cp /var/www/deploy/taobao/taobao-backend/stage_settings.py.bk /var/www/deploy/taobao/taobao-backend/shopmanager/override_settings.py
workdir /var/www/deploy/taobao/taobao-backend/shopmanager
run blueware-admin generate-config BAAGUgBTVAs065dBFQpCVFgfC06fb3VaWUgEVlMFG49d7QlVGgkNH1cB843eBwBJB1RPAQI= blueware.ini
run cd /etc/supervisor/conf.d;ln -s /var/www/deploy/taobao/taobao-backend/config/gunicorn.conf
run cd /etc/supervisor/conf.d;ln -s /var/www/deploy/taobao/taobao-backend/config/celeryd.conf