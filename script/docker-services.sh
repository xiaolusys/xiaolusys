
################# docker sentry ####################


################# docker gitlab redis #####################
#docker run --name gitlab-redis -d \
#    --volume /srv/docker/gitlab/redis:/var/lib/redis \
#    sameersbn/redis:latest

################# docker gitlab #####################
#docker run --name gitlab -d \
#    -p `ifconfig eth0 | awk '/inet addr/{print substr($2,6)}'`:10080:80 \
#    -p `ifconfig eth1 | awk '/inet addr/{print substr($2,6)}'`:10022:22 \
#    --link gitlab-redis:redisio \
#    --env 'GITLAB_HOST=git.xiaolumm.com' \
#    --env 'GITLAB_SSH_HOST=dev.xiaolumm.com'  --env 'GITLAB_SSH_PORT=10022' \
#    --env 'GITLAB_SECRETS_DB_KEY_BASE=Wx9qVJhrVtfbTt4cPrP7m7sjgRC9R4c9shPwthHTK9k9ffCkXmK7cNsV4XtFTXzw' \
#    --env 'DB_ADAPTER=mysql2' \
#    --env 'DB_HOST=rdsvrl2p9pu6536n7d99.mysql.rds.aliyuncs.com'  \
#    --env 'DB_NAME=gitlab' --env 'DB_USER=gitlabdba' \
#    --env 'DB_PASS=xiaolu2016' \
#    --volume /srv/docker/gitlab/gitlab:/home/git/data  sameersbn/gitlab:8.7.0






