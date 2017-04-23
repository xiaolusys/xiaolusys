from registry.aliyuncs.com/xiaolu-img/xiaolusys-base:a3464951565161bb9831e48e6e7a1b1fa5476c64

run mkdir -p /var/log/taobao;mkdir -p /var/www/deploy/taobao;mkdir -p /data/log/django
add . /var/www/deploy/taobao/xiaolusys
workdir /var/www/deploy/taobao/xiaolusys

