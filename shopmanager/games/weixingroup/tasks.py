# -*- coding:utf-8 -*-
from celery.task import task
from flashsale.promotion.models.freesample import DownloadUnionidRecord


@task()
def task_write_download_unionid_record(fans):
    customer = fans.get_from_customer()
    uni_key = '/'.join([str(customer.id), str(fans.unionid)])
    if not DownloadUnionidRecord.objects.filter(uni_key=uni_key).exist():
        record = DownloadUnionidRecord(
            from_customer=customer.id,
            ufrom=DownloadUnionidRecord.ACTIVITY,
            uni_key=uni_key,
            unionid=fans.unionid,
            headimgurl=fans.head_img_url,
            nick=fans.nick
        )
        record.save()
