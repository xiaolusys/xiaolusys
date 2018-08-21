#!/bin/bash

apt-get update
apt-get install -y gcc libxml2-dev libxslt1-dev python-dev libmysqld-dev libjpeg-dev python-pip supervisor git

mkdir -p /var/log/taobao
mkdir -p /var/www/deploy/taobao
cd /var/www/deploy/taobao

git clone user1@youni.f3322.org:repo/taobao-backend.git

pip install virtualenv -i http://pypi.douban.com/simple

cd /var/www/deploy/taobao/taobao-backend
cp prod_settings.py shopmanager/
virtualenv ve

ve/bin/pip install --no-use-wheel -r requirements_production.txt -i http://pypi.douban.com/simple --trusted-host pypi.douban.com

ve/bin/pip install --trusted-host pypi.oneapm.com -i http://pypi.oneapm.com/simple --upgrade blueware
ve/bin/blueware-admin generate-config BAAGUgBTVAs065dBFQpCVFgfC06fb3VaWUgEVlMFG49d7QlVGgkNH1cB843eBwBJB1RPAQI= shopmanager/blueware.ini

cd /etc/supervisor/conf.d/
ln -s /var/www/deploy/taobao/taobao-backend/config/gunicorn.conf
ln -s /var/www/deploy/taobao/taobao-backend/config/celeryd.conf
supervisorctl update
