#-*- coding:utf8 -*-
from django.db import models
from shopback import paramconfig as pcfg
from shopback.archives.models import Supplier,PurchaseType,Deposite
from shopback.categorys.models import ProductCategory
from shopback.items.models import Product,ProductSku

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
    (pcfg.PURCHASE_APPROVAL,'审批')
)

PRODUCT_STATUS = (
    (pcfg.NORMAL,'使用'),
    (pcfg.DELETE,'作废'),
)


class Purchase(models.Model):
    """ 采购单 """
    
    supplier     = models.ForeignKey(Supplier,null=True,blank=True,related_name='purchases',verbose_name='供应商')
    deposite     = models.ForeignKey(Deposite,null=True,blank=True,related_name='purchases',verbose_name='仓库')
    type         = models.ForeignKey(PurchaseType,null=True,blank=True,related_name='purchases',verbose_name='采购类型')
    
    forecast_time = models.DateTimeField(null=True,blank=True,verbose_name='预测到货时间')
    post_time    = models.DateTimeField(null=True,blank=True,verbose_name='业务时间')

    created      = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='创建日期')
    modified     = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='修改日期')
    
    status       = models.CharField(max_length=32,db_index=True,choices=PURCHASE_STATUS,default=pcfg.PURCHASE_DRAFT,verbose_name='采购状态')
    extra_info   = models.TextField(blank=True,verbose_name='备注')
    
    class Meta:
        db_table = 'shop_purchases_purchase'
        verbose_name='采购单'

    def __unicode__(self):
        return 'CGD%d'%self.id
    
    
class PurchaseItem(models.Model):
    """ 采购子订单 """
    
    purchase     = models.ForeignKey(Purchase,related_name='purchase_items',verbose_name='采购单')
    supplier_item_id = models.CharField(max_length=64,blank=True,verbose_name='供应商产品编码')
    
    product      = models.ForeignKey(Product,related_name='purchase_items',verbose_name='采购产品')
    product_sku  = models.ForeignKey(ProductSku,related_name='purchase_items',verbose_name='采购产品规格')
    
    purchase_num = models.IntegerField(null=True,verbose_name='采购数量')
    discount     = models.FloatField(null=True,verbose_name='折扣')
    
    price        = models.FloatField(null=True,verbose_name='价格')

    total_fee    = models.FloatField(null=True,verbose_name='总费用')
    payment      = models.FloatField(null=True,verbose_name='实付')
    
    created      = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='创建日期')
    modified     = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='修改日期')
    
    status       = models.CharField(max_length=32,db_index=True,choices=PURCHASE_ITEM_STATUS,default=pcfg.PURCHASE_DRAFT,verbose_name='状态')
    extra_info   = models.TextField(blank=True,verbose_name='备注')
    
    class Meta:
        db_table = 'shop_purchases_item'
        verbose_name='采购子订单'
    
    def __unicode__(self):
        return 'CGZD%d'%self.id
    
    
class PurchaseStorage(models.Model):
    """ 采购入库单 """
    
    supplier     = models.ForeignKey(Supplier,null=True,blank=True,related_name='purchase_storages',verbose_name='供应商')
    deposite     = models.ForeignKey(Deposite,null=True,blank=True,related_name='purchases_storages',verbose_name='仓库')
    type         = models.ForeignKey(PurchaseType,null=True,blank=True,related_name='purchases_storages',verbose_name='采购类型')
    
    forecast_time = models.DateTimeField(null=True,blank=True,verbose_name='预计到货日期')
    post_time    = models.DateTimeField(null=True,blank=True,verbose_name='实际到货日期')
    
    purchase     = models.ForeignKey(Purchase,null=True,blank=True,related_name='purchases_storages',verbose_name='关联采购单')
    
    created      = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='创建日期')
    modified     = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='修改日期')
    
    status       = models.CharField(max_length=32,db_index=True,choices=PURCHASE_STORAGE_STATUS,default=pcfg.PURCHASE_DRAFT,verbose_name='状态')
    extra_info   = models.TextField(blank=True,verbose_name='备注')
    
    class Meta:
        db_table = 'shop_purchases_storage'
        verbose_name='采购入库单'

    def __unicode__(self):
        return 'RKD%d'%self.id
    

class PurchaseStorageItem(models.Model):
    """ 采购入库详情单 """
    
    purchase_storage     = models.ForeignKey(PurchaseStorage,related_name='purchase_storage_items',verbose_name='关联入库单')
    supplier_item_id     = models.CharField(max_length=64,blank=True,verbose_name='提供商商品编号')
    
    product      = models.ForeignKey(Product,related_name='purchase_storage_items',verbose_name='采购商品')
    product_sku  = models.ForeignKey(ProductSku,related_name='purchase_storage_items',verbose_name='采购商品规格')
    
    storage_num = models.IntegerField(null=True,verbose_name='入库数量')
    
    created      = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='创建日期')
    modified     = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='修改日期')
    
    status       = models.CharField(max_length=32,db_index=True,choices=PURCHASE_STORAGE_STATUS,default=pcfg.PURCHASE_DRAFT,verbose_name='入库状态')
    extra_info   = models.TextField(blank=True,verbose_name='备注')
    
    class Meta:
        db_table = 'shop_purchases_storageitem'
        verbose_name='采购入库详情单'
    
    def __unicode__(self):
        return 'RKZD%d'%self.id
    
        

    
    
    