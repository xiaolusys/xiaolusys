#!/bin/bash

cd /var/www/deploy/taobao/taobao-backend

git pull origin master

supervisorctl restart gunicorn
supervisorctl restart celery


