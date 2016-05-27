# -*- coding:utf-8 -*-
from django.db import models
from django.db.models.signals import post_save

from core.models import BaseModel


#class PurchaseDetail(BaseModel):
#    purchase_order_unikey = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'订货单唯一ID')
#
#    outer_id = models.CharField(max_length=20, blank=True, verbose_name=u'商品编码')
#    outer_sku_id = models.CharField(max_length=20, blank=True, verbose_name=u'规格ID')
#    product_id = models.CharField(db_index=True, max_length=32, verbose_name=u'商品id')
#    
#    outer_id = models.CharField(max_length=32, db_index=True, verbose_name=u'产品外部编码')
#    product_name = models.CharField(max_length=128, verbose_name=u'产品名称')
#    
#    buy_quantity = models.IntegerField(default=0, verbose_name=u'产品数量')
#    buy_unitprice = models.FloatField(default=0, verbose_name=u'买入价格')
#    total_price = models.FloatField(default=0, verbose_name=u'单项总价')
#    arrival_quantity = models.IntegerField(default=0, verbose_name=u'正品数量')
#    inferior_quantity = models.IntegerField(default=0, verbose_name=u'次品数量')
#    non_arrival_quantity = models.IntegerField(default=0, verbose_name=u'未到数量')
#
#
#    class Meta:
#        db_table = 'flashsale_dinghuo_purchase_detail'
#        app_label = 'dinghuo'
#        verbose_name = u'v2/订货明细'
#        verbose_name_plural = u'v2/订货明细表'
#
#    def __unicode__(self):
#        return "%s-%s/%s" % (self.id, self.product_name, self.sku_properties_name)



class PurchaseRecord(BaseModel):
    EFFECT = 1
    CANCEL = 2
    ASSIGN = 3
    STATUS = ((EFFECT, u'有效'),(CANCEL, u'退货取消'),(ASSIGN, u'匹配取消'))
    
    package_sku_item_id = models.IntegerField(default=0,db_index=True, verbose_name=u'包裹ID')
    oid =  models.CharField(max_length=32,db_index=True, verbose_name=u'sku交易单号')

    uni_key = models.CharField(max_length=32, unique=True, verbose_name=u'唯一id ') #sale_order_id + num_of_purchase_try
    purchase_order_unikey =  models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'订货单唯一id')

    outer_id = models.CharField(max_length=32, db_index=True, verbose_name=u'产品外部编码') #color-level code
    outer_sku_id = models.CharField(max_length=32, blank=True, verbose_name=u'规格ID') #size-level code

    sku_id = models.CharField(max_length=32, db_index=True, verbose_name=u'sku商品id') #sku-level id
    title = models.CharField(max_length=128, verbose_name=u'颜色级产品名称') #color-level product name
    sku_properties_name = models.CharField(max_length=16, blank=True, verbose_name=u'购买规格') #sku level info (size)

    num =  models.IntegerField(default=0, verbose_name=u'订购量')
    status =  models.IntegerField(choices=STATUS,default=EFFECT,db_index=True, verbose_name=u'状态')

    initial_book =  models.BooleanField(default=False,db_index=True, verbose_name=u'是否已订货')

    
    class Meta:
        db_table = 'flashsale_dinghuo_purchase_record'
        app_label = 'dinghuo'
        verbose_name = u'v2/订单订货记录'
        verbose_name_plural = u'v2/订单订货记录表'        

    def __unicode__(self):
        return "%s-%s/%s" % (self.id, self.product_name, self.sku_properties_name)
    
