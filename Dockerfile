from registry.aliyuncs.com/xiaolu-img/xiaolusys-base:aacd234029a29f5a96a02e0771b27ecdbfc1d6f7

run mkdir -p /var/log/taobao;mkdir -p /var/www/deploy/taobao;mkdir -p /data/log/django
add . /var/www/deploy/taobao/xiaolusys
workdir /var/www/deploy/taobao/xiaolusys

