# -*- coding:utf8 -*-
import time
import datetime
import json
import urllib2
import cgi
from lxml import etree
from StringIO import StringIO
from celery.task import task
from celery.task.sets import subtask
from celery import Task

from django.db.models import Q

from .models import WeixinUserAward
from .service import WeixinSaleService


class NotifyReferalAwardTask(Task):
    max_retries = 1

    def run(self, user_openid):
        wx_service = WeixinSaleService(user_openid)

        wx_service.notifyReferalAward()


class NotifyParentAwardTask(Task):
    max_retries = 1

    def run(self):

        end_remind_time = datetime.datetime.now() - datetime.timedelta(seconds=10 * 60)

        remind_filter = Q(remind_count__gte=3) | Q(remind_time__lte=end_remind_time)
        wx_awards = WeixinUserAward.objects.filter(remind_filter,
                                                   is_notify=False,
                                                   is_share=False)

        for award in wx_awards:
            try:
                wx_service = WeixinSaleService(award.user_openid)
                wx_service.notifyAward()

                award.is_notify = True
                award.save()
            except Exception, exc:
                pass
