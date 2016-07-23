# -*- coding:utf-8 -*-
from celery.task import task
from flashsale.promotion.models.freesample import DownloadUnionidRecord, DownloadMobileRecord


@task()
def task_write_download_unionid_record(fans):
    from flashsale.xiaolumm.models import XiaoluMama
    if XiaoluMama.objects.filter(openid=fans.union_id).first():
        return
    customer = fans.get_from_customer()
    uni_key = '/'.join([str(customer.id), str(fans.union_id)])
    if not DownloadUnionidRecord.objects.filter(uni_key=uni_key).exists():
        record = DownloadUnionidRecord(
            from_customer=customer.id,
            ufrom=DownloadMobileRecord.ACTIVITY,
            uni_key=uni_key,
            unionid=fans.union_id,
            headimgurl=fans.head_img_url,
            nick=fans.nick
        )
        record.save()
