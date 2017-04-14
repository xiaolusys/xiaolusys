from registry.aliyuncs.com/xiaolu-img/xiaolusys-base:f8c653222e8a9d9d0cbe301bec4446957500e235

run mkdir -p /var/log/taobao;mkdir -p /var/www/deploy/taobao;mkdir -p /data/log/django
add . /var/www/deploy/taobao/xiaolusys
workdir /var/www/deploy/taobao/xiaolusys

