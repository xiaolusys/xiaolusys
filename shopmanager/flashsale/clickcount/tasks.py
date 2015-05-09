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
            if clicks:  # 如果昨天有对应的小鹿妈妈的点击存在
                clickcount = ClickCount()  # 新建一个统计实例 待写入    # 一定要在写入之前 创建  在 如果在FOR循环外面 则会出现后来数据重写到同一个 中
                clickcount.number = xiaolumama.id  # 写ID到统计表
                clickcount.name = xiaolumama.weikefu  # 写名字到统计表
                frequency = clicks.count()  # 点击数量
                nop = clicks.values('openid').distinct().count()  # 点击人数
                clickcount.administrator = xiaolumama.manager  # 接管人
                clickcount.frequency = frequency
                clickcount.nop = nop
                clickcount.date = yesterday
                clickcount.save()

    except Exception, exc:
        raise task_Record_User_Click.retry(exc=exc)