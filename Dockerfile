from registry.aliyuncs.com/xiaolu-img/xiaolusys-base:0495d3d9afc505d2c1326bbe98a87aec3ce9ab71

run mkdir -p /var/log/taobao;mkdir -p /var/www/deploy/taobao;mkdir -p /data/log/django
add . /var/www/deploy/taobao/taobao-backend
workdir /var/www/deploy/taobao/taobao-backend/shopmanager

run blueware-admin generate-config BAAGUgBTVAs065dBFQpCVFgfC06fb3VaWUgEVlMFG49d7QlVGgkNH1cB843eBwBJB1RPAQI= blueware.ini
