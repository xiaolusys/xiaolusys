#-*- coding:utf8 -*-
from django.db import models
from shopback import paramconfig as pcfg
from shopback.suppliers.models import Supplier
from shopback.categorys.models import ProductCategory


PURCHASE_STATUS = (
    (pcfg.PURCHASE_DRAFT,'草稿'),
    (pcfg.PURCHASE_APPROVAL,'审批'),
    (pcfg.PURCHASE_FINISH,'完成'),
    (pcfg.PURCHASE_INVALID,'作废'),
)

PURCHASE_ITEM_STATUS = (
    (pcfg.PURCHASE_DRAFT,'草稿'),
    (pcfg.PURCHASE_APPROVAL,'审批'),
    (pcfg.PURCHASE_RETURN,'退货'),
    (pcfg.PURCHASE_CLOSE,'退货关闭'),
    (pcfg.PURCHASE_FINISH,'完成'),
    (pcfg.PURCHASE_INVALID,'作废'),
    (pcfg.PURCHASE_REWORD,'返修'),
    (pcfg.PURCHASE_REWORDOVER,'返修结束'),
)

PURCHASE_STORAGE_STATUS = (
    (pcfg.PURCHASE_DRAFT,'草稿'),
    (pcfg.PURCHASE_APPROVAL,'审批'),
    (pcfg.PURCHASE_DRAFT,'草稿'),
)

PRODUCT_STATUS = (
    (pcfg.NORMAL,'使用'),
    (pcfg.DELETE,'删除'),
)



class PurchaseProduct(models.Model):
    """ 采购产品 """
    
    outer_id     = models.CharField(max_length=64)
    name         = models.CharField(max_length=128,blank=True)
    
    category     = models.ForeignKey(ProductCategory,null=True,blank=True,related_name='purchase_products')
    #stock_num    = models.IntegerField(default=0)
    
    created      = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    modified     = models.DateTimeField(null=True,blank=True,auto_now=True)
    
    status       = models.CharField(max_length=16,db_index=True,choices=PRODUCT_STATUS,default=pcfg.NORMAL)
    
    class Meta:
        db_table = 'shop_purchase_product'
        verbose_name='采购商品'

    def __unicode__(self):
        return '<%s,%s>'%(self.outer_id,self.name)


class PurchaseProductSku(models.Model):
    """ 采购产品规格 """
    
    product      = models.ForeignKey(PurchaseProduct,related_name='purchase_productskus')
    outer_id     = models.CharField(max_length=64)
    properties   = models.CharField(max_length=256,blank=True)
    
    #sku_num      = models.IntegerField(default=0)
    created      = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    modified     = models.DateTimeField(null=True,blank=True,auto_now=True)
    
    status       = models.CharField(max_length=16,db_index=True,choices=PRODUCT_STATUS,default=pcfg.NORMAL)
    
    class Meta:
        db_table = 'shop_purchase_productsku'
        verbose_name='采购商品规格'

    def __unicode__(self):
        return '<%s,%s>'%(self.outer_id,self.properties)


class Deposite(models.Model):
    """ 采购仓库 """
    
    deposite_name = models.CharField(max_length=32,blank=True)
    location     = models.CharField(max_length=32,blank=True)
    
    in_use       = models.BooleanField(default=True)
    extra_info   = models.TextField(blank=True)
    class Meta:
        db_table = 'shop_purchases_deposite'
        verbose_name='仓库'

    def __unicode__(self):
        return self.deposite_name


class PurchaseType(models.Model):
    """ 采购类型 """
    
    type_name    = models.CharField(max_length=32,blank=True)
    in_use       = models.BooleanField(default=True)
    
    extra_info   = models.TextField(blank=True)
    
    class Meta:
        db_table = 'shop_purchases_purchasetype'
        verbose_name='采购类型'

    def __unicode__(self):
        return self.type_name
    

class Purchase(models.Model):
    """ 采购单 """
    
    supplier     = models.ForeignKey(Supplier,null=True,blank=True,related_name='purchases')
    deposite     = models.ForeignKey(Deposite,null=True,blank=True,related_name='purchases')
    type         = models.ForeignKey(PurchaseType,null=True,blank=True,related_name='purchases')
    
    forecast_time = models.DateTimeField(null=True,blank=True)
    post_time    = models.DateTimeField(null=True,blank=True)

    created      = models.DateTimeField(auto_now=True)
    modified     = models.DateTimeField(auto_now_add=True)
    
    status       = models.CharField(max_length=32,db_index=True,choices=PURCHASE_STATUS,default=pcfg.PURCHASE_DRAFT)
    extra_info   = models.TextField(blank=True)
    
    class Meta:
        db_table = 'shop_purchases_purchase'
        verbose_name='采购单'

    def __unicode__(self):
        return 'CGD%d'%self.id
    
    
    
class PurchaseItem(models.Model):
    """ 采购子订单 """
    
    purchase     = models.ForeignKey(Purchase,related_name='purchase_items')
    supplier_item_id = models.CharField(max_length=64,blank=True)
    
    product      = models.ForeignKey(PurchaseProduct,related_name='purchase_items')
    product_sku  = models.ForeignKey(PurchaseProductSku,related_name='purchase_items')
    
    purchase_num = models.IntegerField(null=True)
    discount     = models.FloatField(null=True)
    
    price        = models.FloatField(null=True)

    total_fee    = models.FloatField(null=True)
    payment      = models.FloatField(null=True)
    
    created      = models.DateTimeField(null=True,blank=True,auto_now=True)
    modified     = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    
    status       = models.CharField(max_length=32,db_index=True,choices=PURCHASE_ITEM_STATUS,default=pcfg.PURCHASE_DRAFT)
    extra_info   = models.TextField(blank=True)
    
    class Meta:
        db_table = 'shop_purchases_item'
        verbose_name='采购子订单'
    
    def __unicode__(self):
        return 'CGZD%d'%self.id
    
    
class PurchaseStorage(models.Model):
    """ 采购入库单 """
    
    supplier     = models.ForeignKey(Supplier,null=True,blank=True,related_name='purchase_storages')
    deposite     = models.ForeignKey(Deposite,null=True,blank=True,related_name='purchases_storages')
    type         = models.ForeignKey(PurchaseType,null=True,blank=True,related_name='purchases_storages')
    
    forecast_time = models.DateTimeField(null=True,blank=True)
    post_time    = models.DateTimeField(null=True,blank=True)
    
    purchase     = models.ForeignKey(Purchase,null=True,blank=True,related_name='purchases_storages')
    
    created      = models.DateTimeField(auto_now=True)
    modified     = models.DateTimeField(auto_now_add=True)
    
    status       = models.CharField(max_length=32,db_index=True,choices=PURCHASE_STORAGE_STATUS,default=pcfg.PURCHASE_DRAFT)
    extra_info   = models.TextField(blank=True)
    
    class Meta:
        db_table = 'shop_purchases_storage'
        verbose_name='采购入库单'

    def __unicode__(self):
        return 'RKD%d'%self.id
    

class PurchaseStorageItem(models.Model):
    """ 采购入库详情单 """
    
    purchase_storage     = models.ForeignKey(PurchaseStorage,related_name='purchase_storageitems')
    supplier_item_id     = models.CharField(max_length=64,blank=True)
    
    product      = models.ForeignKey(PurchaseProduct,related_name='purchase_storageitems')
    product_sku  = models.ForeignKey(PurchaseProductSku,related_name='purchase_storageitems')
    
    storage_num = models.IntegerField(null=True)
    
    created      = models.DateTimeField(null=True,blank=True,auto_now=True)
    modified     = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    
    status       = models.CharField(max_length=32,db_index=True,choices=PURCHASE_STORAGE_STATUS,default=pcfg.PURCHASE_DRAFT)
    extra_info   = models.TextField(blank=True)
    
    class Meta:
        db_table = 'shop_purchases_storageitem'
        verbose_name='采购入库详情单'
    
    def __unicode__(self):
        return 'RKZD%d'%self.id
    
        

    
    
    