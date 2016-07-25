# coding=utf-8
import datetime
from flashsale.pay.models.user import Customer
from celery.task import task
from flashsale.promotion.models.freesample import AppDownloadRecord

@task()
def task_update_appdownload_record():
    time_begin = datetime.datetime.now() - datetime.timedelta(days=2)
    union_ids = [u['unionid'] for u in Customer.objects.filter(created__gt=time_begin).values('unionid')]
    AppDownloadRecord.objects.filter(status=AppDownloadRecord.UNUSE, unionid__in=union_ids).update(
        status=AppDownloadRecord.USED)
