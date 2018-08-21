# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from core.fields import JSONCharMyField

from ..managers import WeixinProductManager


class WXProduct(models.Model):
    UP_SHELF = 1
    DOWN_SHELF = 2

    UP_ACTION = 1
    DOWN_ACTION = 0

    PRODUCT_STATUS = (
        (UP_SHELF, u'上架'),
        (DOWN_SHELF, u'下架')
    )

    product_id = models.CharField(max_length=32, primary_key=True, verbose_name=u'商品ID')

    product_name = models.CharField(max_length=64, verbose_name=u'商品标题')
    product_img = models.CharField(max_length=512, verbose_name=u'商品图片')

    product_base = JSONCharMyField(max_length=3000, blank=True, default={}, verbose_name=u'图文信息')

    sku_list = JSONCharMyField(max_length=3000, blank=True, default={}, verbose_name=u'规格信息')

    attrext = JSONCharMyField(max_length=1000, blank=True, default={}, verbose_name=u'附加信息')

    delivery_info = JSONCharMyField(max_length=200, blank=True, default={}, verbose_name=u'发货信息')

    sync_stock = models.BooleanField(default=True, verbose_name=u'同步库存')

    status = models.IntegerField(null=False, default=0, choices=PRODUCT_STATUS, verbose_name=u'是否上架')

    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')

    objects = WeixinProductManager()

    class Meta:
        db_table = 'shop_weixin_product'
        app_label = 'weixin'
        verbose_name = u'微信小店商品'
        verbose_name_plural = u'微信小店商品列表'

    def __unicode__(self):
        return u'<WXProduct:%s>' % (self.product_id)


class WXSkuProperty(models.Model):
    sku_id = models.CharField(max_length=32, unique=True, verbose_name=u'规格ID')

    name = models.CharField(max_length=64, verbose_name=u'规格名称')

    class Meta:
        db_table = 'shop_weixin_skuproperty'
        app_label = 'weixin'
        verbose_name = u'微信商品属性'
        verbose_name_plural = u'微信商品属性列表'

    def __unicode__(self):
        return u'<WXSkuProperty:%s>' % self.sku_id


class WXProductSku(models.Model):
    UP_SHELF = 1
    DOWN_SHELF = 2

    PRODUCT_STATUS = (
        (UP_SHELF, u'上架'),
        (DOWN_SHELF, u'下架')
    )

    sku_id = models.CharField(max_length=64, verbose_name=u'规格ID')
    product = models.ForeignKey(WXProduct, verbose_name=u'微信商品')

    outer_id = models.CharField(max_length=64, blank=True, verbose_name=u'商品编码')
    outer_sku_id = models.CharField(max_length=64, blank=True, verbose_name=u'规格编码')

    sku_name = models.CharField(max_length=64, verbose_name=u'规格名称')
    sku_img = models.CharField(max_length=512, verbose_name=u'规格图片')
    sku_num = models.IntegerField(default=0, verbose_name=u"规格数量")

    sku_price = models.FloatField(default=0, verbose_name=u'售价')
    ori_price = models.FloatField(default=0, verbose_name=u'原价')

    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')

    status = models.IntegerField(null=False, default=UP_SHELF,
                                 choices=PRODUCT_STATUS,
                                 verbose_name=u'是否上架')

    class Meta:
        db_table = 'shop_weixin_productsku'
        unique_together = ("sku_id", "product")
        app_label = 'weixin'
        verbose_name = u'微信小店规格'
        verbose_name_plural = u'微信小店规格列表'

    def __unicode__(self):
        return u'<WXProductSku:%s,%s>' % (self.outer_id, self.outer_sku_id)

    @classmethod
    def getSkuNameBySkuId(cls, sku_id):

        sku_name = ''
        skuid_list = [s for s in sku_id.split(';') if s.strip()]
        skuid_list.reverse()
        for sku_tair in skuid_list:
            k_id, vid = sku_tair.split(':')

            if not vid.startswith('$'):
                wx_skus = WXSkuProperty.objects.filter(sku_id=vid)
                if wx_skus.count() > 0:
                    sku_name += wx_skus[0].name
            else:
                vid = vid.strip('$')
                sku_name += vid

        return sku_name

    @property
    def sku_image(self):
        return self.sku_img.split('?')[0]


from shopapp.signals import signal_wxorder_pay_confirm


class WXOrder(models.Model):
    WX_WAIT_PAY = 1
    WX_WAIT_SEND = 2
    WX_WAIT_CONFIRM = 3
    WX_FINISHED = 5
    WX_CLOSE = 6
    WX_FEEDBACK = 8

    WXORDER_STATUS = (
        (WX_WAIT_PAY, u'待付款'),
        (WX_WAIT_SEND, u'待发货'),
        (WX_WAIT_CONFIRM, u'待确认收货'),
        (WX_FINISHED, u'已完成'),
        (WX_CLOSE, u'已关闭'),
        (WX_FEEDBACK, u'维权中')
    )

    order_id = models.CharField(max_length=32, primary_key=True, verbose_name=u'订单ID')

    trans_id = models.CharField(max_length=32, blank=True, verbose_name=u'交易ID')
    seller_id = models.CharField(max_length=32, db_index=True, verbose_name=u'商家ID')

    buyer_openid = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u'买家OPENID')
    buyer_nick = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'买家昵称')

    order_total_price = models.IntegerField(default=0, verbose_name=u'订单总价(分)')
    order_express_price = models.IntegerField(default=0, verbose_name=u'订单运费(分)')
    order_create_time = models.DateTimeField(blank=True, null=True, verbose_name=u'创建时间')
    order_status = models.IntegerField(choices=WXORDER_STATUS, db_index=True, default=WX_WAIT_PAY, verbose_name=u'订单状态')

    receiver_name = models.CharField(max_length=64, blank=True, verbose_name=u'收货人')
    receiver_province = models.CharField(max_length=24, blank=True, verbose_name=u'省')
    receiver_city = models.CharField(max_length=24, blank=True, verbose_name=u'市')
    receiver_zone = models.CharField(max_length=24, blank=True, verbose_name=u'区')
    receiver_address = models.CharField(max_length=128, blank=True, verbose_name=u'地址')
    receiver_mobile = models.CharField(max_length=24, blank=True, verbose_name=u'手机')
    receiver_phone = models.CharField(max_length=24, blank=True, verbose_name=u'电话')

    product_id = models.CharField(max_length=64, blank=True, verbose_name=u'商品ID')
    product_name = models.CharField(max_length=64, blank=True, verbose_name=u'商品名')
    product_price = models.IntegerField(default=0, verbose_name=u'商品价格(分)')
    product_sku = models.CharField(max_length=128, blank=True, verbose_name=u'商品SKU')
    product_count = models.IntegerField(default=0, verbose_name=u'商品个数')
    product_img = models.CharField(max_length=512, blank=True, verbose_name=u'商品图片')

    delivery_id = models.CharField(max_length=32, blank=True, verbose_name=u'运单ID')
    delivery_company = models.CharField(max_length=16, blank=True, verbose_name=u'物流公司编码')

    class Meta:
        db_table = 'shop_weixin_order'
        app_label = 'weixin'
        verbose_name = u'微信小店订单'
        verbose_name_plural = u'微信小店订单列表'

    def __unicode__(self):
        return u'<WXOrder:%s,%s>' % (self.order_id, self.buyer_nick)

    @classmethod
    def mapTradeStatus(cls, wx_order_status):

        from shopback import paramconfig as pcfg
        if wx_order_status == cls.WX_WAIT_SEND:
            return pcfg.WAIT_SELLER_SEND_GOODS

        elif wx_order_status == cls.WX_WAIT_CONFIRM:
            return pcfg.WAIT_BUYER_CONFIRM_GOODS

        elif wx_order_status == cls.WX_FINISHED:
            return pcfg.TRADE_FINISHED

        elif wx_order_status == cls.WX_CLOSE:
            return pcfg.TRADE_CLOSED

        elif wx_order_status == cls.WX_FEEDBACK:
            return pcfg.WAIT_BUYER_CONFIRM_GOODS

        return pcfg.WAIT_BUYER_PAY

    @classmethod
    def mapOrderStatus(cls, wx_order_status):

        from shopback import paramconfig as pcfg
        if wx_order_status == cls.WX_WAIT_SEND:
            return pcfg.WAIT_SELLER_SEND_GOODS

        elif wx_order_status == cls.WX_WAIT_CONFIRM:
            return pcfg.WAIT_BUYER_CONFIRM_GOODS

        elif wx_order_status == cls.WX_FINISHED:
            return pcfg.TRADE_FINISHED

        elif wx_order_status == cls.WX_CLOSE:
            return pcfg.TRADE_CLOSED

        elif wx_order_status == cls.WX_FEEDBACK:
            return pcfg.TRADE_REFUNDING

        return pcfg.WAIT_BUYER_PAY

    def confirm_payment(self):

        signal_wxorder_pay_confirm.send(sender=WXOrder, obj=self)


class WXLogistic(models.Model):
    company_name = models.CharField(max_length=16, blank=True, verbose_name=u'快递名称')
    origin_code = models.CharField(max_length=16, blank=True, verbose_name=u'原始编码')
    company_code = models.CharField(max_length=16, blank=True, verbose_name=u'快递编码')

    class Meta:
        db_table = 'shop_weixin_logistic'
        app_label = 'weixin'
        verbose_name = u'微信小店快递'
        verbose_name_plural = u'微信小店快递列表'
