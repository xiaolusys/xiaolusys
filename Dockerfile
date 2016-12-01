from registry.aliyuncs.com/xiaolu-img/xiaolusys-base:8c68e521ce4367c7da2c8616d66f7d0673f632f3

run mkdir -p /var/log/taobao;mkdir -p /var/www/deploy/taobao;mkdir -p /data/log/django
add . /var/www/deploy/taobao/xiaolusys
workdir /var/www/deploy/taobao/xiaolusys

run blueware-admin generate-config BAAGUgBTVAs065dBFQpCVFgfC06fb3VaWUgEVlMFG49d7QlVGgkNH1cB843eBwBJB1RPAQI= blueware.ini
