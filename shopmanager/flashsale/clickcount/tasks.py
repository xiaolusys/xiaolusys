# -*- encoding:utf8 -*-
import time
import datetime
import calendar
from django.conf import settings
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings

from flashsale.xiaolumm.models import XiaoluMama, Clicks
from .models import ClickCount

import logging

__author__ = 'linjie'

logger = logging.getLogger('celery.handler')


@task(max_retry=3, default_retry_delay=5)
def task_Record_User_Click():
    try:
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        time_from = datetime.datetime(yesterday.year, yesterday.month, yesterday.day)  # 生成带时间的格式  开始时间
        time_to = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)  # 停止时间

        xiaolumamas = XiaoluMama.objects.all()  # 所有小鹿妈妈们

        for xiaolumama in xiaolumamas:  #
            clicks = Clicks.objects.filter(linkid=xiaolumama.id).filter(created__gt=time_from,
                                                                        created__lt=time_to)  # 根据代理的id过滤出点击表中属于该代理的点击
            clickcount, state = ClickCount.objects.get_or_create(date=yesterday,
                                                                 number=xiaolumama.id)  # 在点击统计表中找今天的记录 如果 有number和小鹿妈妈的id相等的 说明已经该记录已经统计过了
            clickcount.name = xiaolumama.weikefu  # 写名字到统计表
            frequency = clicks.count()  # 点击数量
            nop = clicks.values('openid').distinct().count()  # 点击人数
            clickcount.administrator = xiaolumama.manager  # 接管人
            clickcount.frequency = frequency
            clickcount.nop = nop
            clickcount.save()

    except Exception, exc:
        raise task_Record_User_Click.retry(exc=exc)