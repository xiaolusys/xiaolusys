from registry.aliyuncs.com/xiaolu-img/xiaolusys-base:0cf32a415c707decacd13620edf64aa361472af6

run mkdir -p /var/log/taobao;mkdir -p /var/www/deploy/taobao
add . /var/www/deploy/taobao/taobao-backend
workdir /var/www/deploy/taobao/taobao-backend/shopmanager
run blueware-admin generate-config BAAGUgBTVAs065dBFQpCVFgfC06fb3VaWUgEVlMFG49d7QlVGgkNH1cB843eBwBJB1RPAQI= blueware.ini
