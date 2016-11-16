# -*- coding:utf8 -*-
from __future__ import unicode_literals

import time
import json
import datetime
from django.db import models
from shopback.signals import user_logged_in
from shopapp.jingdong import apis
import logging

logger = logging.getLogger('django.request')


class JDShop(models.Model):
    shop_id = models.CharField(max_length=32, primary_key=True, verbose_name=u'店铺ID')
    vender_id = models.CharField(max_length=32, blank=True, verbose_name=u'商家ID')
    shop_name = models.CharField(max_length=32, blank=True, verbose_name=u'店铺名称')
    open_time = models.DateTimeField(blank=True, null=True, verbose_name=u'开店时间')

    logo_url = models.CharField(max_length=512, blank=True, verbose_name=u'LOGO')
    brief = models.TextField(max_length=2000, blank=True, verbose_name=u'店铺简介')
    category_main = models.BigIntegerField(null=True, verbose_name=u'主营类目ID')
    category_main_name = models.CharField(max_length=2000, blank=True, verbose_name=u'主营类目名称')

    order_updated = models.DateTimeField(blank=True, null=True,
                                         verbose_name="订单增量更新时间")

    refund_updated = models.DateTimeField(blank=True, null=True,
                                          verbose_name="维权增量更新时间")

    class Meta:
        db_table = 'shop_jingdong_shop'
        app_label = 'jingdong'
        verbose_name = u'京东商铺'
        verbose_name_plural = u'京东商铺列表'

    def __unicode__(self):
        return u'<%s>' % (self.shop_name)

    def updateOrderUpdated(self, updated):
        self.order_updated = updated
        self.save()

    def updateRefundUpdated(self, updated):
        self.refund_updated = updated
        self.save()


class JDLogistic(models.Model):
    logistics_id = models.CharField(max_length=32, primary_key=True, verbose_name=u'物流ID')
    logistics_name = models.CharField(max_length=32, blank=True, verbose_name=u'物流名称')
    logistics_remark = models.CharField(max_length=128, blank=True, verbose_name=u'备注')
    sequence = models.CharField(max_length=32, blank=True, verbose_name=u'序列')
    company_code = models.CharField(max_length=32, blank=True, verbose_name=u'公司编码')

    class Meta:
        db_table = 'shop_jingdong_logistic'
        app_label = 'jingdong'
        verbose_name = u'京东物流'
        verbose_name_plural = u'京东物流列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.logistics_id, self.logistics_name)


class JDOrder(models.Model):
    SOP = '22'
    LBP = '23'
    SOPL = '25'

    ORDER_TYPE = ((SOP, 'SOP'),
                  (LBP, 'LBP'),
                  (SOPL, 'SOPL'),
                  )

    PAY_TYPE_COD = '1'
    PAY_TYPE_POST = '2'
    PAY_TYPE_SELF = '3'
    PAY_TYPE_ONLINE = '4'
    PAY_TYPE_CTF = '5'
    PAY_TYPE_BANK = '6'

    PAY_TYPE = ((PAY_TYPE_COD, u'货到付款'),
                (PAY_TYPE_POST, u'邮局汇款'),
                (PAY_TYPE_SELF, u'自提'),
                (PAY_TYPE_ONLINE, u'在线支付'),
                (PAY_TYPE_CTF, u'公司转账'),
                (PAY_TYPE_BANK, u'银行转账'),
                )

    ORDER_STATE_WSTO = 'WAIT_SELLER_STOCK_OUT'
    #    ORDER_STATE_STDC = 'SEND_TO_DISTRIBUTION_CENER'
    #    ORDER_STATE_DCR  = 'DISTRIBUTION_CENTER_RECEIVED'
    ORDER_STATE_WGRC = 'WAIT_GOODS_RECEIVE_CONFIRM'
    #    ORDER_STATE_RC   = 'RECEIPTS_CONFIRM'
    #    ORDER_STATE_WSD  = 'WAIT_SELLER_DELIVERY'
    ORDER_STATE_FL = 'FINISHED_L'
    ORDER_STATE_TC = 'TRADE_CANCELED'
    ORDER_STATE_LOCKED = 'LOCKED'

    ORDER_STATE = ((ORDER_STATE_WSTO, u'等待出库'),
                   #                  (ORDER_STATE_STDC,u'发往配送中心'),
                   #                  (ORDER_STATE_DCR,u'配送中心已收货'),
                   (ORDER_STATE_WGRC, u'等待确认收货'),
                   #                  (ORDER_STATE_RC,u'收款确认'),
                   #                  (ORDER_STATE_WSD,u'等待发货'),
                   (ORDER_STATE_FL, u'完成'),
                   (ORDER_STATE_TC, u'取消'),
                   (ORDER_STATE_LOCKED, u'已锁定'),
                   )

    order_id = models.CharField(max_length=32, primary_key=True, verbose_name=u'订单ID')
    shop = models.ForeignKey(JDShop, verbose_name=u'所属商铺')

    pay_type = models.CharField(max_length=16, blank=True
                                , choices=PAY_TYPE, verbose_name=u'支付方式')
    order_total_price = models.FloatField(default=0.0, verbose_name=u'总金额')
    order_payment = models.FloatField(default=0.0, verbose_name=u'实付款')
    order_seller_price = models.FloatField(default=0.0, verbose_name=u'货款金额')
    freight_price = models.FloatField(default=0.0, verbose_name=u'运费')
    seller_discount = models.FloatField(default=0.0, verbose_name=u'优惠金额')

    delivery_type = models.CharField(max_length=32, blank=True, verbose_name=u'送货类型')
    invoice_info = models.CharField(max_length=256, blank=True, verbose_name=u'发票信息')

    order_start_time = models.DateTimeField(blank=True, null=True, verbose_name=u'下单时间')
    order_end_time = models.DateTimeField(blank=True, null=True, verbose_name=u'结单时间')
    modified = models.DateTimeField(blank=True, null=True, verbose_name=u'修改时间')
    payment_confirm_time = models.DateTimeField(blank=True, null=True, verbose_name=u'付款时间')

    consignee_info = models.TextField(max_length=1000, blank=True, verbose_name=u'收货人信息')
    item_info_list = models.TextField(max_length=10000, blank=True, verbose_name=u'商品列表')
    coupon_detail_list = models.TextField(max_length=2000, blank=True, verbose_name=u'优惠列表')
    return_order = models.CharField(max_length=2, blank=True, verbose_name=u'换货标识')

    pin = models.CharField(max_length=64, blank=True, verbose_name=u'账号信息')
    balance_used = models.FloatField(default=0.0, verbose_name=u'余额支付金额')

    logistics_id = models.CharField(max_length=128, blank=True, verbose_name=u'物流公司ID')
    waybill = models.CharField(max_length=128, blank=True, verbose_name=u'运单号')
    vat_invoice_info = models.CharField(max_length=512, blank=True, verbose_name=u'增值税发票')
    parent_order_id = models.CharField(max_length=32, blank=True, verbose_name=u'父订单号')

    order_remark = models.CharField(max_length=512, blank=True, verbose_name=u'买家备注')
    vender_remark = models.CharField(max_length=1000, blank=True, verbose_name=u'卖家备注')

    order_type = models.CharField(max_length=8, blank=True,
                                  choices=ORDER_TYPE, verbose_name=u'订单类型')
    order_state = models.CharField(max_length=32, blank=True,
                                   choices=ORDER_STATE, verbose_name=u'订单状态')
    order_state_remark = models.CharField(max_length=128, blank=True, verbose_name=u'订单状态说明')

    class Meta:
        db_table = 'shop_jingdong_order'
        app_label = 'jingdong'
        verbose_name = u'京东订单'
        verbose_name_plural = u'京东订单列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.order_id, self.pin)

    @classmethod
    def mapTradeStatus(cls, jd_trade_status):

        from shopback import paramconfig as pcfg
        if jd_trade_status == cls.ORDER_STATE_WSTO:
            return pcfg.WAIT_SELLER_SEND_GOODS

        elif jd_trade_status == cls.ORDER_STATE_WGRC:
            return pcfg.WAIT_BUYER_CONFIRM_GOODS

        elif jd_trade_status == cls.ORDER_STATE_FL:
            return pcfg.TRADE_FINISHED

        elif jd_trade_status == cls.ORDER_STATE_TC:
            return pcfg.TRADE_CLOSED

        return pcfg.WAIT_BUYER_PAY


class JDProduct(models.Model):
    NEVER_UP = 'NEVER_UP'
    CUSTORMER_DOWN = 'CUSTORMER_DOWN'
    SYSTEM_DOWN = 'SYSTEM_DOWN'
    ON_SALE = 'ON_SALE'
    AUDIT_AWAIT = 'AUDIT_AWAIT'
    AUDIT_FAIL = 'AUDIT_FAIL'
    WARE_STATUS = (
        (NEVER_UP, u'从未上架'),
        (CUSTORMER_DOWN, u'自主下架'),
        (SYSTEM_DOWN, u'系统下架'),
        (ON_SALE, u'在售'),
        (AUDIT_AWAIT, u'待审核'),
        (AUDIT_FAIL, u'审核不通过'),
    )

    DELETE = 'DELETE'
    INVALID = 'INVALID'
    VALID = 'VALID'
    STATUS = (
        (DELETE, u'删除'),
        (INVALID, u'无效'),
        (VALID, u'有效')
    )

    ware_id = models.BigIntegerField(primary_key=True, verbose_name=u'商品ID')
    vender_id = models.CharField(max_length=32, blank=True, verbose_name=u'商家ID')
    shop_id = models.CharField(max_length=32, blank=True, verbose_name=u'店铺ID')
    spu_id = models.CharField(max_length=32, blank=True, verbose_name=u'SPU ID')
    cid = models.CharField(max_length=32, blank=True, verbose_name=u'分类ID')

    outer_id = models.CharField(max_length=32, blank=True, verbose_name=u'SKU外部ID')
    skus = models.TextField(max_length=10000, blank=True, verbose_name=u'商品SKU')
    title = models.CharField(max_length=64, blank=True, verbose_name=u'标题')

    item_num = models.CharField(max_length=32, blank=True, verbose_name=u'货号')
    upc_code = models.CharField(max_length=16, blank=True, verbose_name=u'UPC编码')
    transport_id = models.BigIntegerField(null=True, verbose_name=u'运费模板')
    online_time = models.DateTimeField(blank=True, null=True, verbose_name=u'最后上架时间')
    offline_time = models.DateTimeField(blank=True, null=True, verbose_name=u'最后下架时间')

    attributes = models.CharField(max_length=1024, blank=True, verbose_name=u'属性列表')
    desc = models.CharField(max_length=2000, blank=True, verbose_name=u'商品描述')
    producter = models.CharField(max_length=32, blank=True, verbose_name=u'生产厂商')
    wrap = models.CharField(max_length=32, blank=True, verbose_name=u'包装规格')
    cubage = models.CharField(max_length=16, blank=True, verbose_name=u'长:宽:高')
    weight = models.CharField(max_length=8, blank=True, verbose_name=u'重量')
    pack_listing = models.CharField(max_length=128, blank=True, verbose_name=u'包装清单')
    service = models.CharField(max_length=128, blank=True, verbose_name=u'售后服务')

    cost_price = models.FloatField(default=0.0, verbose_name=u'进货价')
    market_price = models.FloatField(default=0.0, verbose_name=u'市场价')
    jd_price = models.FloatField(default=0.0, verbose_name=u'京东价')
    stock_num = models.IntegerField(default=0, verbose_name=u'库存')
    logo = models.CharField(max_length=256, blank=True, verbose_name=u'主图')
    creator = models.CharField(max_length=32, blank=True, verbose_name=u'录入人')
    created = models.DateTimeField(blank=True, null=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(blank=True, null=True, verbose_name=u'修改日期')

    is_pay_first = models.BooleanField(default=True, verbose_name=u'先款后货')
    is_can_vat = models.BooleanField(default=True, verbose_name=u'发票限制')

    ware_big_small_model = models.IntegerField(null=True, verbose_name=u'商品件型')
    ware_pack_type = models.IntegerField(null=True, verbose_name=u'商品包装')
    ad_content = models.CharField(max_length=256, blank=True, verbose_name=u'广告语')

    sync_stock = models.BooleanField(default=True, verbose_name=u'同步库存')

    shop_categorys = models.CharField(max_length=128, blank=True, verbose_name=u'店内分类')
    status = models.CharField(max_length=8, blank=True
                              , choices=STATUS, verbose_name=u'状态')
    ware_status = models.CharField(max_length=16, blank=True
                                   , choices=WARE_STATUS, verbose_name=u'商品状态')

    class Meta:
        db_table = 'shop_jingdong_product'
        app_label = 'jingdong'
        verbose_name = u'京东商品'
        verbose_name_plural = u'京东商品列表'

    def __unicode__(self):
        return u'<%d,%s>' % (self.ware_id, self.item_num)


def add_jingdong_user(sender, user, top_session,
                      top_parameters, *args, **kwargs):
    """docstring for user_logged_in"""

    from shopback.users.models import User
    profiles = User.objects.filter(type=User.SHOP_TYPE_JD, user=user)
    if profiles.count() == 0:
        return

    profile = profiles[0]
    user_dict = apis.jd_seller_vender_info_get(
        access_token=top_parameters['access_token'])

    profile.visitor_id = user_dict['vender_id']
    profile.nick = profile.nick or user_dict['shop_name']

    profile.save()

    shop_dict = apis.jd_vender_shop_query(
        access_token=top_parameters['access_token'])

    jd_shop, state = JDShop.objects.get_or_create(shop_id=shop_dict['shop_id'])

    for k, v in shop_dict.iteritems():
        hasattr(jd_shop, k) and setattr(jd_shop, k, v)

    jd_shop.open_time = datetime.datetime.fromtimestamp(shop_dict['open_time'] / 1000)
    jd_shop.save()

    # 初始化系统数据
    from .tasks import pullJDLogisticByVenderidTask, pullJDProductByVenderidTask

    pullJDProductByVenderidTask(user_dict['vender_id'], ware_status=1)
    pullJDProductByVenderidTask(user_dict['vender_id'], ware_status=2)

    pullJDLogisticByVenderidTask(user_dict['vender_id'])


user_logged_in.connect(add_jingdong_user,
                       sender='jingdong',
                       dispatch_uid='jingdong_logged_in')
