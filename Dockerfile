from registry.aliyuncs.com/xiaolu-img/xiaolusys-base:a9e257caa2a9286714027bef36777855c4b902b8

run mkdir -p /var/log/taobao;mkdir -p /var/www/deploy/taobao;mkdir -p /data/log/django
add . /var/www/deploy/taobao/xiaolusys
workdir /var/www/deploy/taobao/xiaolusys

