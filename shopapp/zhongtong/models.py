# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from shopback import paramconfig as pcfg

SYS_TRADE_STATUS = (
    (pcfg.WAIT_AUDIT_STATUS, u'问题单'),
    (pcfg.WAIT_PREPARE_SEND_STATUS, u'待发货准备'),
    (pcfg.WAIT_CHECK_BARCODE_STATUS, u'待扫描验货'),
    (pcfg.WAIT_SCAN_WEIGHT_STATUS, u'待扫描称重'),
    (pcfg.FINISHED_STATUS, u'已完成'),
    (pcfg.INVALID_STATUS, u'已作废'),
    (pcfg.ON_THE_FLY_STATUS, u'飞行模式'),
    (pcfg.REGULAR_REMAIN_STATUS, u'定时提醒'),
)
TAOBAO_TRADE_STATUS = (
    (pcfg.TRADE_NO_CREATE_PAY, u'订单创建'),
    (pcfg.WAIT_BUYER_PAY, u'待付款'),
    (pcfg.WAIT_SELLER_SEND_GOODS, u'待发货'),
    (pcfg.WAIT_BUYER_CONFIRM_GOODS, u'待确认收货'),
    (pcfg.TRADE_BUYER_SIGNED, u'货到付款签收'),
    (pcfg.TRADE_FINISHED, u'交易成功'),
    (pcfg.TRADE_CLOSED, u'退款交易关闭'),
    (pcfg.TRADE_CLOSED_BY_TAOBAO, u'未付款关闭'),
)
TRADE_TYPE = (
    (pcfg.TAOBAO_TYPE, u'淘宝&商城'),
    (pcfg.FENXIAO_TYPE, u'淘宝分销'),
    (pcfg.SALE_TYPE, u'小鹿特卖'),
    (pcfg.JD_TYPE, u'京东商城'),
    (pcfg.YHD_TYPE, u'一号店'),
    (pcfg.DD_TYPE, u'当当商城'),
    (pcfg.SN_TYPE, u'苏宁易购'),
    (pcfg.WX_TYPE, u'微信小店'),
    (pcfg.AMZ_TYPE, u'亚马逊'),
    (pcfg.DIRECT_TYPE, u'内售'),
    (pcfg.REISSUE_TYPE, u'补发'),
    (pcfg.EXCHANGE_TYPE, u'退换货'),
)


# 订单列表
class ZTOOrderList(models.Model):
    YES = 0
    NO = 1

    STATUS_CHOICES = ((YES, U'已打印'),
                      (NO, U'未打印'),)

    SYS_TRADE_STATUS = SYS_TRADE_STATUS
    TAOBAO_TRADE_STATUS = TAOBAO_TRADE_STATUS
    TRADE_TYPE = TRADE_TYPE

    yid = models.CharField(max_length=64, blank=True, db_index=True,
                           verbose_name=u'原单ID')
    cus_oid = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u'客户订单编号')
    out_sid = models.CharField(max_length=64, db_index=True,
                               blank=True, verbose_name=u'物流单号')
    type = models.CharField(max_length=32, choices=TRADE_TYPE,
                            blank=True, verbose_name=u'订单类型')
    weight = models.CharField(max_length=10, blank=True, verbose_name=u'包裹重量')
    created = models.DateTimeField(null=True, blank=True, verbose_name=u'生成日期')
    consign_time = models.DateTimeField(null=True, blank=True, verbose_name=u'发货日期')
    logistics_company = models.CharField(max_length=64, db_index=True, default=u'中通速递',
                                         blank=True, verbose_name=u'物流公司')
    receiver_name = models.CharField(max_length=25,
                                     blank=True, verbose_name=u'收货人姓名')
    receiver_state = models.CharField(max_length=16, blank=True, verbose_name=u'省')
    receiver_city = models.CharField(max_length=16, blank=True, verbose_name=u'市')
    receiver_district = models.CharField(max_length=16, blank=True, verbose_name=u'区/县')

    receiver_address = models.CharField(max_length=128, blank=True, verbose_name=u'详细地址')
    receiver_zip = models.CharField(max_length=10, blank=True, verbose_name=u'邮编')
    receiver_mobile = models.CharField(max_length=24, db_index=True,
                                       blank=True, verbose_name=u'手机')
    receiver_phone = models.CharField(max_length=20, db_index=True,
                                      blank=True, verbose_name=u'电话')
    order_status = models.CharField(max_length=32, choices=TAOBAO_TRADE_STATUS,
                                    blank=True, verbose_name=u'订单状态')
    sys_status = models.CharField(max_length=32, db_index=True,
                                  choices=SYS_TRADE_STATUS, blank=True,
                                  default='', verbose_name=u'系统状态')
    status = models.IntegerField(choices=STATUS_CHOICES, default=NO, verbose_name=u'打印状态')
    remarke = models.CharField(max_length=20, blank=True, verbose_name=u'备注')

    class Meta:
        db_table = 'ztoorderlist'
        app_label = 'zhongtong'
        verbose_name = u'订单列表'
        verbose_name_plural = u'中通订单列表'

    def __unicode__(self):
        return '<%s,%s,%s>' % (self.yid, self.cus_oid, self.out_sid)


# 打印记录表
class PrintRecord(models.Model):
    out_sid = models.CharField(max_length=64, db_index=True,
                               blank=True, verbose_name=u'物流单号')
    record_name = models.CharField(max_length=25,
                                   blank=True, verbose_name=u'打印员')
    record_time = models.DateTimeField(null=True, blank=True, verbose_name=u'打印日期')
    weight = models.CharField(max_length=10, blank=True, verbose_name=u'包裹重量')
    receiver_name = models.CharField(max_length=25,
                                     blank=True, verbose_name=u'收货人姓名')
    receiver_state = models.CharField(max_length=16, blank=True, verbose_name=u'省')
    receiver_city = models.CharField(max_length=16, blank=True, verbose_name=u'市')
    receiver_district = models.CharField(max_length=16, blank=True, verbose_name=u'区/县')

    receiver_address = models.CharField(max_length=128, blank=True, verbose_name=u'详细地址')
    receiver_zip = models.CharField(max_length=10, blank=True, verbose_name=u'邮编')
    receiver_mobile = models.CharField(max_length=24, db_index=True,
                                       blank=True, verbose_name=u'手机')
    receiver_phone = models.CharField(max_length=20, db_index=True,
                                      blank=True, verbose_name=u'电话')

    class Meta:
        db_table = 'ztoprintrecord'
        app_label = 'zhongtong'
        verbose_name = u'打印记录'
        verbose_name_plural = u'打印记录表'

    def __unicode__(self):
        return self.out_sid
