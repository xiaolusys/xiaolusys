#!/bin/bash
################################################
#cd /var/www/deploy/taobao/taobao-backend/shopmanager
#git pull origin master
#\cp -r -a ../prod_settings.py .
#python manage.py collectstatic
#supervisorctl restart gunicorn
#supervisorctl restart celery
################################################

PUBLISH_HOST=(
root@admin.xiaolumm.com
root@proxy.huyi.so
root@sale.huyi.so 
)

CMD="cd /var/www/deploy/taobao/taobao-backend/shopmanager && git pull origin master && \cp -r -a ../prod_settings.py.bk ./prod_settings.py && ../ve/bin/python manage.py collectstatic --noinput && supervisorctl update && supervisorctl restart gunicorn &&  (supervisorctl restart celery || true)" 

#CMD="lsb_release -a"

if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
  echo "Usage: $0 ($CMD)" >&2
  exit 1
fi

for i in "${PUBLISH_HOST[@]}"; 
do
     echo -e '..................Start publish server:' $i `date "+%Y-%m-%d %H:%M:%S"`
     ssh $i $CMD || exit 1
done
 
cat <<EOF
Publish server code success.
EOF
