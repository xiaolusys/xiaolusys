from registry.aliyuncs.com/xiaolu-img/xiaolusys-base:68b751bc9268ecd8acefad51236635acdb0b7e02

run mkdir -p /var/log/taobao;mkdir -p /var/www/deploy/taobao
add . /var/www/deploy/taobao/taobao-backend
workdir /var/www/deploy/taobao/taobao-backend/shopmanager
run blueware-admin generate-config BAAGUgBTVAs065dBFQpCVFgfC06fb3VaWUgEVlMFG49d7QlVGgkNH1cB843eBwBJB1RPAQI= blueware.ini
