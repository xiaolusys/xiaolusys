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
        appdownloads = AppDownloadRecord.objects.all().order_by('created')
        print "starting move download record to new table: total count is %s" % appdownloads.count()
        # 分享人用户id/手机号　or 分享人用户id/用户unionid
        unionid_count = 0
        mobile_count = 0
        for appdownload in appdownloads:
            if appdownload.unionid:
                uni_key = '/'.join([str(appdownload.from_customer), appdownload.unionid])
                record = DownloadUnionidRecord.objects.filter(uni_key=uni_key).exists()
                if not record:
                    if unionid_count % 100 == 0:
                        print "create new union record: %s" % uni_key
                    unionid_count += 1
                    cursor = connection.cursor()
                    sql = "insert into flashsale_promotion_download_unionid_record (" \
                          "from_customer, " \
                          "ufrom, " \
                          "uni_key, " \
                          "unionid, " \
                          "headimgurl, " \
                          "nick, " \
                          "created, " \
                          "modified " \
                          " ) values ('%s','%s','%s','%s','%s','%s','%s','%s')" % (appdownload.from_customer,
                                                                                   DownloadMobileRecord.QRCODE,
                                                                                   uni_key,
                                                                                   appdownload.unionid,
                                                                                   appdownload.headimgurl,
                                                                                   appdownload.nick,
                                                                                   appdownload.created.strftime(
                                                                                       '%Y-%m-%d %H:%M:%S'),
                                                                                   appdownload.modified.strftime(
                                                                                       '%Y-%m-%d %H:%M:%S'))
                    cursor.execute(sql)
                    cursor.close()
                else:
                    # 记录存在则修改该记录的最后时间到　迁移的数据上
                    if record.created < datetime.datetime(2016, 7, 4, 18, 0, 0):
                        record.created = appdownload.created
                        record.modified = appdownload.modified
                        update_model_fields(record, update_fields=['created', 'modified'])

            elif appdownload.mobile:
                uni_key = '/'.join([str(appdownload.from_customer), appdownload.mobile])
                record = DownloadMobileRecord.objects.filter(uni_key=uni_key).exists()
                if not record:
                    if mobile_count % 10 == 0:
                        print "create new mobile record: %s" % uni_key
                    mobile_count += 1

                    cursor = connection.cursor()
                    sql = "insert into flashsale_promotion_download_mobile_record (" \
                          "from_customer, " \
                          "mobile, " \
                          "ufrom, " \
                          "uni_key, " \
                          "created, " \
                          "modified" \
                          " ) values ('%s','%s','%s','%s','%s','%s')" % (appdownload.from_customer,
                                                                         appdownload.mobile,
                                                                         DownloadMobileRecord.QRCODE,
                                                                         uni_key,
                                                                         appdownload.created.strftime(
                                                                             '%Y-%m-%d %H:%M:%S'),
                                                                         appdownload.modified.strftime(
                                                                             '%Y-%m-%d %H:%M:%S'))
                    cursor.execute(sql)
                    cursor.close()
                else:
                    if record.created < datetime.datetime(2016, 7, 4, 18, 0, 0):
                        record.created = appdownload.created
                        record.modified = appdownload.modified
                        update_model_fields(record, update_fields=['created', 'modified'])
        print "new create record mobile_count %s and unionid_count %s" % (mobile_count, unionid_count)
