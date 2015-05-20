# -*- coding:utf-8 -*-
from django.db import models
from flashsale.dinghuo import paramconfig as pcfg
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey

ORDER_PRODUCT_STATUS = (
    (pcfg.SUBMITTING, u'提交中'),
    (pcfg.APPROVAL, u'审核'),
    (pcfg.ZUOFEI, u'作废'),
    (pcfg.COMPLETED, u'验货完成'),
)


class OrderList(models.Model):
    
    id = BigIntegerAutoField(primary_key=True)
    buyer_name = models.CharField(default="",max_length=32, verbose_name=u'买手')
    order_amount = models.FloatField(default=0, verbose_name=u'金额')
    supplier_name = models.CharField(default="",blank=True, max_length=128, verbose_name=u'供应商')
    express_company = models.CharField(default="", blank=True, max_length=32, verbose_name=u'快递公司')
    express_no = models.CharField(default="",blank=True, max_length=32, verbose_name=u'快递单号')
    receiver = models.CharField(default="", max_length=32, verbose_name=u'仓库负责人')
    costofems = models.IntegerField(default=0, verbose_name=u'快递费用')
    status = models.CharField(max_length=32, verbose_name=u'订货单状态', choices=ORDER_PRODUCT_STATUS)
    created = models.DateField(auto_now_add=True, verbose_name=u'订货日期')
    updated = models.DateField(auto_now_add=True, verbose_name=u'更新日期')
    note = models.TextField(default="",blank=True, verbose_name=u'备注信息')

    class Meta:
        db_table = 'suplychain_flashsale_orderlist'
        verbose_name = u'订货表'
        verbose_name_plural = u'订货表'

    def costofems_cash(self):
        return self.costofems / 100.0
    costofems_cash.allow_tags = True
    costofems_cash.short_description = u"快递费用"

    def __unicode__(self):
        return '<%s,%s,%s>' % (str(self.id or ''), self.id, self.buyer_name)


class OrderDetail(models.Model):
    
    id = BigIntegerAutoField(primary_key=True)
    
    orderlist = BigIntegerForeignKey(OrderList, verbose_name=u'订单编号')
    product_id = models.CharField(max_length=32, verbose_name=u'商品id')
    outer_id = models.CharField(max_length=32, verbose_name=u'产品外部编码')
    product_name = models.CharField(max_length=128, verbose_name=u'产品名称')
    chichu_id = models.CharField(max_length=32, verbose_name=u'规格id')
    product_chicun = models.CharField(max_length=100, verbose_name=u'产品尺寸')
    buy_quantity = models.IntegerField(default=0, verbose_name=u'产品数量')
    buy_unitprice = models.FloatField(default=0, verbose_name=u'买入价格')
    total_price = models.FloatField(default=0, verbose_name=u'单项总价')
    arrival_quantity = models.IntegerField(default=0, verbose_name=u'到货数量')
    created = models.DateField(auto_now_add=True, verbose_name=u'生成日期')
    updated = models.DateField(auto_now_add=True, verbose_name=u'更新日期')


    class Meta:
        db_table = 'suplychain_flashsale_orderdetail'
        verbose_name = u'订货明细表'
        verbose_name_plural = u'订货明细表'

    def __unicode__(self):
        return self.product_id


class orderdraft(models.Model):
    buyer_name = models.CharField(default="None", max_length=32, verbose_name=u'买手')
    product_id = models.CharField(max_length=32, verbose_name=u'商品id')
    outer_id = models.CharField(max_length=32, verbose_name=u'产品外部编码')
    product_name = models.CharField(max_length=128, verbose_name=u'产品名称')
    chichu_id = models.CharField(max_length=32, verbose_name=u'规格id')
    product_chicun = models.CharField(default="", max_length=20, verbose_name=u'产品尺寸')
    buy_unitprice = models.FloatField(default=0, verbose_name=u'买入价格')
    buy_quantity = models.IntegerField(default=0, verbose_name=u'产品数量')
    created = models.DateField(auto_now_add=True, verbose_name=u'生成日期')

    class Meta:
        db_table = 'suplychain_flashsale_orderdraft'
        verbose_name = u'草稿表'
        verbose_name_plural = u'草稿表'

    def __unicode__(self):
        return self.product_name
