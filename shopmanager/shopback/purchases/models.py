#-*- coding:utf8 -*-
from django.db import models
from shopback.suppliers.models import Supplier
from shopback.items.models import Product,ProductSku


PURCHASE_DRAFT    = 'DRAFT'
PURCHASE_APPROVAL = 'APPROVAL'
PURCHASE_ARRIVAL  = 'ARRIVAL'
PURCHASE_RETURN   = 'RETURN'
PURCHASE_FINISH   = 'FINISH'
PURCHASE_INVALID  = 'INVALID'  
PURCHASE_CLOSE    = 'CLOSE'  #退货确认后该交易关闭
PURCHASE_REWORD   = 'REWORD' #返修
PURCHASE_REWORDOVER  = 'REWORDOVER' #返修结束


PURCHASE_STATUS = (
    (PURCHASE_DRAFT,'草稿'),
    (PURCHASE_APPROVAL,'审批'),
    (PURCHASE_ARRIVAL,'到货'),
    (PURCHASE_CLOSE,'退货关闭'),
    (PURCHASE_FINISH,'完成'),
    (PURCHASE_INVALID,'作废'),
)

PURCHASE_ITEM_STATUS = (
    (PURCHASE_DRAFT,'草稿'),
    (PURCHASE_APPROVAL,'审批'),
    (PURCHASE_ARRIVAL,'到货'),
    (PURCHASE_RETURN,'退货'),
    (PURCHASE_CLOSE,'退货关闭'),
    (PURCHASE_FINISH,'完成'),
    (PURCHASE_INVALID,'作废'),
    (PURCHASE_REWORD,'返修'),
    (PURCHASE_REWORDOVER,'返修结束'),
)


class Deposite(models.Model):
    
    deposite_name = models.CharField(max_length=32,blank=True)
    location     = models.CharField(max_length=32,blank=True)
    
    in_use       = models.BooleanField(default=True)
    extra_info   = models.TextField(blank=True)
    class Meta:
        db_table = 'shop_purchases_deposite'

    def __unicode__(self):
        return self.deposite_name


class PurchaseType(models.Model):
    
    type_name    = models.CharField(max_length=32,blank=True)
    in_use       = models.BooleanField(default=True)
    
    extra_info   = models.TextField(blank=True)
    
    class Meta:
        db_table = 'shop_purchases_purchasetype'

    def __unicode__(self):
        return self.type_name
    

class Purchase(models.Model):

    supplier     = models.ForeignKey(Supplier,null=True,related_name='purchases')
    deposite     = models.ForeignKey(Deposite,null=True,related_name='purchases')
    type         = models.ForeignKey(PurchaseType,null=True,related_name='purchases')
    
    forecast_time = models.DateTimeField(null=True,blank=True)
    post_time    = models.DateTimeField(null=True,blank=True)

    created      = models.DateTimeField(auto_now=True)
    modified     = models.DateTimeField(auto_now_add=True)
    
    status       = models.CharField(max_length=32,db_index=True,choices=PURCHASE_STATUS,default=PURCHASE_DRAFT)
    extra_info   = models.TextField(blank=True)
    
    class Meta:
        db_table = 'shop_purchases_purchase'

    def __unicode__(self):
        return self.supplier.supplier_name+self.type.type_name
    
    
    
class PurchaseItem(models.Model):
    
    supplier_item_id = models.CharField(max_length=64,blank=True)
    
    product      = models.ForeignKey(Product,null=True,related_name='purchase_items')
    product_sku  = models.ForeignKey(ProductSku,null=True,related_name='purchase_items')
    
    purchase_num = models.IntegerField(null=True)
    discount     = models.FloatField(null=True)
    
    price        = models.FloatField(null=True)

    total_fee    = models.FloatField(null=True)
    payment      = models.FloatField(null=True)
    
    created      = models.DateTimeField(null=True,blank=True,auto_now=True)
    modified     = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    
    status       = models.CharField(max_length=32,db_index=True,choices=PURCHASE_ITEM_STATUS,default=PURCHASE_DRAFT)
    extra_info   = models.TextField(blank=True)
    
    class Meta:
        db_table = 'shop_purchases_item'

    def __unicode__(self):
        return self.product.name
    
    
    
    