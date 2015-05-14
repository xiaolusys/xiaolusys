# -*- encoding:utf8 -*-
import time
import datetime
import calendar
from django.conf import settings
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopapp.weixin.models import WXOrder
from flashsale.xiaolumm.models import XiaoluMama, Clicks
from .models import ClickCount

import logging

__author__ = 'linjie'

logger = logging.getLogger('celery.handler')


@task(max_retry=3, default_retry_delay=5)
def task_Record_User_Click(pre_day=1):
    
    yesterday = datetime.date.today() - datetime.timedelta(days=pre_day)
    time_from = datetime.datetime(yesterday.year, yesterday.month, yesterday.day)  # 生成带时间的格式  开始时间
    time_to = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)  # 停止时间

    xiaolumamas = XiaoluMama.objects.all()  # 所有小鹿妈妈们

    for xiaolumama in xiaolumamas:  #
        clicks = Clicks.objects.filter(created__gt=time_from, created__lt=time_to,
                                       linkid=xiaolumama.id)  # 根据代理的id过滤出点击表中属于该代理的点击

        clickcount, state = ClickCount.objects.get_or_create(date=yesterday,
                                                             linkid=xiaolumama.id)  # 在点击统计表中找今天的记录 如果 有number和小鹿妈妈的id相等的 说明已经该记录已经统计过了
        clickcount.weikefu = xiaolumama.weikefu  # 写名字到统计表
        click_num = clicks.count()  # 点击数量
        user_num = clicks.values('openid').distinct().count()  # 点击人数
        clickcount.username = xiaolumama.manager  # 接管人
        clickcount.click_num = click_num
        clickcount.mobile = xiaolumama.mobile
        clickcount.user_num = user_num
        clickcount.save()

