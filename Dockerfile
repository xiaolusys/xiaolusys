from registry.aliyuncs.com/xiaolu-img/xiaolusys-base:235e58c03bdb3dcf98ba092fe7dc6359e97320bc

run mkdir -p /var/log/taobao;mkdir -p /var/www/deploy/taobao;mkdir -p /data/log/django
add . /var/www/deploy/taobao/xiaolusys
workdir /var/www/deploy/taobao/xiaolusys

