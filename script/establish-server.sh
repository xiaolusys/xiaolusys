#/bin/bash

sudo apt-get install curl
echo "DOCKER_OPTS=\"--registry-mirror=https://n5fb0zgg.mirror.aliyuncs.com\"" | sudo tee -a /etc/default/docker
service docker restart
docker login --username=己美网络 registry.aliyuncs.com

# 添加数据访问白名单
# 添加xiaolusys对应的drone Public Key 到本地ssh authorizen_keys
# 修改.drone.yml 添加当前主机host
# 配置nginx site.conf 添加当前域名
# 配置xiaolusys oneapm-ci-agent 

