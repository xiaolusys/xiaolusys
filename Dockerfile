from registry.aliyuncs.com/xiaolu-img/xiaolusys-base:bd7878c11f89b2c8c6489bf36dd6c46716e9cf7e

run mkdir -p /var/log/taobao;mkdir -p /var/www/deploy/taobao;mkdir -p /data/log/django
add . /var/www/deploy/taobao/xiaolusys
workdir /var/www/deploy/taobao/xiaolusys

run blueware-admin generate-config BAAGUgBTVAs065dBFQpCVFgfC06fb3VaWUgEVlMFG49d7QlVGgkNH1cB843eBwBJB1RPAQI= blueware.ini
