from ubuntu:14.04
run apt-get update
run apt-get install -y gcc libxml2-dev libxslt1-dev python-dev libmysqld-dev libjpeg-dev python-pip supervisor git

run mkdir -p /var/log/taobao
run mkdir -p /var/www/deploy/taobao
add . /var/www/deploy/taobao/taobao-backend
run cp /var/www/deploy/taobao/taobao-backend/prod_settings.py.bk /var/www/deploy/taobao/taobao-backend/shopmanager/
run pip install virtualenv -i http://pypi.douban.com/simple
workdir /var/www/deploy/taobao/taobao-backend
run virtualenv ve

run ve/bin/pip install --no-use-wheel -r requirements_production.txt -i http://pypi.douban.com/simple --trusted-host pypi.douban.com

run ve/bin/pip install -i http://pypi.oneapm.com/simple --trusted-host pypi.oneapm.com --upgrade blueware
run ve/bin/blueware-admin generate-config BAAGUgBTVAs065dBFQpCVFgfC06fb3VaWUgEVlMFG49d7QlVGgkNH1cB843eBwBJB1RPAQI= shopmanager/blueware.ini

run cd /etc/supervisor/conf.d;ln -s /var/www/deploy/taobao/taobao-backend/config/gunicorn.conf
run cd /etc/supervisor/conf.d;ln -s /var/www/deploy/taobao/taobao-backend/config/celeryd.conf
