# -*- coding:utf8 -*-
from __future__ import absolute_import, unicode_literals

import datetime
from celery import shared_task as task

from django.db.models import Q

from .models import WeixinUserAward
from .service import WeixinSaleService

@task
def task_notify_referal_award(user_openid):
    wx_service = WeixinSaleService(user_openid)
    wx_service.notifyReferalAward()

@task
def task_notify_parent_award():

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
