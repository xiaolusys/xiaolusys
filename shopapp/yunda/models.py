# -*- coding:utf8 -*-
from __future__ import unicode_literals

import re
import datetime
from django.db import models
from shopback.signals import change_addr_signal
from shopback.trades.models import MergeTrade
import logging

logger = logging.getLogger('yunda.handler')

NORMAL = 'normal'
DELETE = 'delete'
YUNDA = 'YUNDA'
YUNDA_QR = 'YUNDA_QR'
YUNDA_CODE = (YUNDA, YUNDA_QR)

JZHW_REGEX = re.compile('^(上海|江苏|浙江|安徽)'.decode('utf8'))

ORDER_STATUS_CHOICES = (
    (NORMAL, U'正常'),
    (DELETE, U'删除'),
)


class BranchZone(models.Model):
    code = models.CharField(max_length=10, db_index=True, blank=True, verbose_name='网点编号')
    name = models.CharField(max_length=64, blank=True, verbose_name='网点名称')
    barcode = models.CharField(max_length=32, blank=True, verbose_name='网点条码')

    class Meta:
        db_table = 'shop_yunda_branch'
        app_label = 'yunda'
        verbose_name = u'韵达分拨网点'
        verbose_name_plural = u'韵达分拨网点'

    def __unicode__(self):
        return '<%s,%s,%s>' % (self.code, self.barcode, self.name)


class ClassifyZone(models.Model):
    state = models.CharField(max_length=32, db_index=True, blank=True, verbose_name='省')
    city = models.CharField(max_length=32, db_index=True, blank=True, verbose_name='市')
    district = models.CharField(max_length=32, db_index=True, blank=True, verbose_name='区')

    branch = models.ForeignKey(BranchZone, null=True, blank=True, related_name='classify_zones', verbose_name='所属网点')
    zone = models.CharField(max_length=64, blank=True, verbose_name='集包网点')

    class Meta:
        db_table = 'shop_yunda_zone'
        app_label = 'yunda'
        verbose_name = u'韵达分拨地址'
        verbose_name_plural = u'韵达分拨地址'

    def __unicode__(self):
        return '<%s,%s>' % (' '.join([self.state, self.city, self.district]), self.branch or '')


class AnonymousYundaCustomer():
    def isNone(self):
        return True

    def isValid(self):
        return False


class YundaCustomer(models.Model):
    name = models.CharField(max_length=64, blank=True, verbose_name=u'客户名')
    code = models.CharField(max_length=16, verbose_name=u'客户代码')

    cus_id = models.CharField(max_length=32, blank=True, verbose_name=u'网点ID')
    company_name = models.CharField(max_length=32, blank=True, verbose_name=u'客户公司名')
    company_trade = models.CharField(max_length=32, blank=True, verbose_name=u'客户经营范围')
    ware_by = models.IntegerField(default=0, verbose_name=u'所属仓库')

    qr_id = models.CharField(max_length=32, blank=True, verbose_name=u'二维码接口ID')
    qr_code = models.CharField(max_length=32, blank=True, verbose_name=u'二维码接口码')

    lanjian_id = models.CharField(max_length=32, blank=True, verbose_name=u'揽件ID')
    lanjian_code = models.CharField(max_length=32, blank=True, verbose_name=u'揽件码')

    ludan_id = models.CharField(max_length=32, blank=True, verbose_name=u'录单ID')
    ludan_code = models.CharField(max_length=32, blank=True, verbose_name=u'录单码')

    sn_code = models.CharField(max_length=32, blank=True, verbose_name=u'设备SN码')
    device_code = models.CharField(max_length=32, blank=True, verbose_name=u'设备手机号')

    contacter = models.CharField(max_length=32, blank=True, verbose_name=u'联络人')
    state = models.CharField(max_length=16, blank=True, verbose_name=u'省')
    city = models.CharField(max_length=16, blank=True, verbose_name=u'市')
    district = models.CharField(max_length=16, blank=True, verbose_name=u'区')

    address = models.CharField(max_length=128, blank=True, verbose_name=u'详细地址')
    zip = models.CharField(max_length=10, blank=True, verbose_name=u'邮编')
    mobile = models.CharField(max_length=20, db_index=True, blank=True, verbose_name=u'手机')
    phone = models.CharField(max_length=20, db_index=True, blank=True, verbose_name=u'电话')

    on_qrcode = models.BooleanField(default=False, verbose_name=u'开启二维码')
    on_lanjian = models.BooleanField(default=False, verbose_name=u'开启揽件')
    on_ludan = models.BooleanField(default=False, verbose_name=u'开启录单')
    on_bpkg = models.BooleanField(default=False, verbose_name=u'开启集包')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    memo = models.CharField(max_length=100, blank=True, verbose_name=u'备注')
    reserveo = models.CharField(max_length=64, blank=True, verbose_name=u'自定义1')
    reservet = models.CharField(max_length=64, blank=True, verbose_name=u'自定义2')

    status = models.CharField(max_length=10, default=NORMAL,
                              choices=ORDER_STATUS_CHOICES, verbose_name=u'状态')

    class Meta:
        db_table = 'shop_yunda_customer'
        unique_together = ("code", "ware_by")
        app_label = 'yunda'
        verbose_name = u'韵达客户'
        verbose_name_plural = u'韵达客户列表'

    def __unicode__(self):
        return '<%s,%s>' % (self.name, self.code)

    def isNone(self):
        return False

    def isValid(self):
        return True


class LogisticOrder(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=u'ID')
    cus_oid = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u'客户订单编号')
    yd_customer = models.ForeignKey(YundaCustomer, verbose_name=u'所属客户')

    out_sid = models.CharField(max_length=64, unique=True, blank=True, verbose_name=u'物流单号')
    parent_package_id = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'大包编号')

    receiver_name = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'收货人姓名')
    receiver_state = models.CharField(max_length=16, blank=True, verbose_name=u'省')
    receiver_city = models.CharField(max_length=16, blank=True, verbose_name=u'市')
    receiver_district = models.CharField(max_length=16, blank=True, verbose_name=u'区')

    receiver_address = models.CharField(max_length=128, blank=True, verbose_name=u'详细地址')
    receiver_zip = models.CharField(max_length=10, blank=True, verbose_name=u'邮编')
    receiver_mobile = models.CharField(max_length=20, db_index=True, blank=True, verbose_name=u'手机')
    receiver_phone = models.CharField(max_length=20, db_index=True, blank=True, verbose_name=u'电话')

    weight = models.CharField(max_length=10, blank=True, verbose_name=u'称重(kg)')
    upload_weight = models.CharField(max_length=10, blank=True, verbose_name=u'计重(kg)')

    weighted = models.DateTimeField(default=datetime.datetime.now, verbose_name=u'称重日期')
    uploaded = models.DateTimeField(null=True, blank=True, verbose_name=u'上传日期')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    valid_code = models.CharField(max_length=4, blank=True, verbose_name=u'校验码')
    dc_code = models.CharField(max_length=8, blank=True, verbose_name=u'分拨号')

    is_jzhw = models.BooleanField(default=False, verbose_name=u'江浙沪皖')
    is_charged = models.BooleanField(default=False, verbose_name=u'揽件')
    sync_addr = models.BooleanField(default=False, verbose_name=u'录单')

    status = models.CharField(max_length=10, default=NORMAL,
                              choices=ORDER_STATUS_CHOICES, verbose_name=u'状态')

    wave_no = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'批次')

    class Meta:
        db_table = 'shop_yunda_order'
        app_label = 'yunda'
        verbose_name = u'韵达订单'
        verbose_name_plural = u'韵达订单列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.cus_oid, self.out_sid)

    def isJZHW(self):
        return JZHW_REGEX.match(self.receiver_state) and True or False


class ParentPackageWeight(models.Model):
    parent_package_id = models.CharField(primary_key=True, max_length=64, verbose_name=u'大包编号')
    weight = models.FloatField(default=0.0, verbose_name=u'称重(kg)')
    upload_weight = models.FloatField(default=0.0, verbose_name=u'计重(kg)')

    weighted = models.DateTimeField(default=datetime.datetime.now, verbose_name=u'称重日期')
    uploaded = models.DateTimeField(default=datetime.datetime.now, verbose_name=u'上传日期')

    destinate = models.CharField(max_length=24, blank=True, verbose_name=u'集包地')

    is_jzhw = models.BooleanField(default=False, verbose_name=u'江浙沪皖')
    is_charged = models.BooleanField(default=False, verbose_name=u'揽件')

    class Meta:
        db_table = 'shop_yunda_ppw'
        app_label = 'yunda'
        verbose_name = u'韵达大包重量记录'
        verbose_name_plural = u'韵达大包重量记录'

    def __unicode__(self):
        return '<%s>' % (self.parent_package_id)


class TodaySmallPackageWeight(models.Model):
    package_id = models.CharField(primary_key=True, max_length=64, verbose_name=u'运单编号')
    parent_package_id = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'大包编号')
    weight = models.FloatField(default=0.0, verbose_name=u'称重(kg)')
    upload_weight = models.FloatField(default=0.0, verbose_name=u'计重(kg)')
    weighted = models.DateTimeField(default=datetime.datetime.now, verbose_name=u'称重日期')
    is_jzhw = models.BooleanField(default=False, verbose_name=u'江浙沪皖')

    class Meta:
        db_table = 'shop_yunda_tspw'
        app_label = 'yunda'
        verbose_name = u'韵达当日小包重量'
        verbose_name_plural = u'韵达当日小包重量'

    def __unicode__(self):
        return '<%s,%s>' % (self.package_id, self.parent_package_id)


class TodayParentPackageWeight(models.Model):
    parent_package_id = models.CharField(primary_key=True, max_length=64, verbose_name=u'大包编号')
    weight = models.FloatField(default=0.0, verbose_name=u'称重(kg)')
    upload_weight = models.FloatField(default=0.0, verbose_name=u'计重(kg)')
    weighted = models.DateTimeField(default=datetime.datetime.now, verbose_name=u'称重日期')
    is_jzhw = models.BooleanField(default=False, verbose_name=u'江浙沪皖')

    class Meta:
        db_table = 'shop_yunda_tppw'
        app_label = 'yunda'
        verbose_name = u'韵达当日大包重量'
        verbose_name_plural = u'韵达当日大包重量'

    def __unicode__(self):
        return '<%s>' % (self.parent_package_id)
