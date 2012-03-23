import re
import time
import datetime
from celery.task import task
from celery.task.sets import subtask
import logging

logger = logging.getLogger('taobao.taoci')


@task()
def getCatsTaocibyCookie(from_date=None,to_date=None,cat_list=None,cookie=None):
    pass