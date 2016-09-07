#!/bin/bash

cp /etc/apt/sources.list /etc/apt/sources.list.bk; cp ./sources.list.trusty /etc/apt/sources.list

sudo apt-get update
sudo apt-get install curl -y
curl -sSL http://acs-public-mirror.oss-cn-hangzhou.aliyuncs.com/docker-engine/internet | sh -
echo "DOCKER_OPTS=\"--registry-mirror=https://n5fb0zgg.mirror.aliyuncs.com\"" | sudo tee -a /etc/default/docker
service docker restart
docker login --username=己美网络 registry.aliyuncs.com -p kzt[***]72




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
