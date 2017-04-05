# coding: utf8
from __future__ import absolute_import, unicode_literals

from shopmanager import celery_app as app

from django_statsd.clients import statsd
from django.db.models import Sum, F, Count, FloatField

from shopapp.smsmgr.models import SMSRecord

@app.task
def task_sms_send_count_gauge_statsd():

    sms_stats = SMSRecord.objects.filter(
        status__in=(SMSRecord.SMS_COMMIT,SMSRecord.SMS_COMPLETE)
    ).values('task_type').annotate(Count('id')).values_list('task_type', 'id__count')

    for task_type, sms_count in sms_stats:
        statsd.gauge('xiaolumm.sms.send.%s'%task_type, sms_count)

