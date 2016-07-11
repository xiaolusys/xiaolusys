# coding=utf-8
__author__ = 'jishu_linjie'
import datetime
from django.db import connection
from django.core.management.base import BaseCommand
from flashsale.promotion.models import AppDownloadRecord
from flashsale.promotion.models_freesample import DownloadMobileRecord, DownloadUnionidRecord
from core.utils.modelutils import update_model_fields


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        将新导入的下载记录　迁移到原来的表中　
        """
        mobiledowns = DownloadMobileRecord.objects.all()
        unioniddowns = DownloadUnionidRecord.objects.all()
        from flashsale.pay.models import Customer

        print "mobile downs count is:%s" % mobiledowns.count()
        for mobiledown in mobiledowns:
            appdownload = AppDownloadRecord.objects.filter(mobile=mobiledown.mobile,
                                                           from_customer=mobiledown.from_customer).first()
            if not appdownload:
                customer = Customer.objects.filter(mobile=mobiledown.mobile, status=Customer.NORMAL).first()
                unionid = customer.unionid if customer else ''
                thumbnail = customer.thumbnail if customer else ''
                nick = customer.nick if customer else ''
                appdownload = AppDownloadRecord(from_customer=mobiledown.from_customer,
                                                unionid=unionid,
                                                headimgurl=thumbnail,
                                                nick=nick,
                                                mobile=mobiledown.mobile,
                                                inner_ufrom=mobiledown.ufrom)
                appdownload.save()
            else:
                update_fields = []
                if appdownload.ufrom != mobiledown.ufrom:
                    appdownload.ufrom = mobiledown.ufrom
                    update_fields.append('ufrom')
                appdownload.modified = datetime.datetime.now()
                update_fields.append('modified')
                update_model_fields(appdownload, update_fields=update_fields)

        print "mobile downs count is:%s" % unioniddowns.count()
        for unioniddown in unioniddowns:
            appdownload = AppDownloadRecord.objects.filter(unionid=unioniddown.unionid,
                                                           from_customer=unioniddown.from_customer).first()
            if not appdownload:
                customer = Customer.objects.filter(unionid=unioniddown.unionid, status=Customer.NORMAL).first()
                unionid = customer.unionid if customer else ''
                thumbnail = customer.thumbnail if customer else ''
                nick = customer.nick if customer else ''
                mobile = customer.mobile if customer else ''
                appdownload = AppDownloadRecord(from_customer=unioniddown.from_customer,
                                                unionid=unionid,
                                                headimgurl=thumbnail,
                                                nick=nick,
                                                mobile=mobile,
                                                inner_ufrom=unioniddown.ufrom)
                appdownload.save()
            else:
                update_fields = []
                if appdownload.ufrom != unioniddown.ufrom:
                    appdownload.ufrom = unioniddown.ufrom
                    update_fields.append('ufrom')
                appdownload.modified = datetime.datetime.now()
                update_fields.append('modified')
                update_model_fields(appdownload, update_fields=update_fields)
