#-*- coding:utf8 -*-
from django.db import models
from django.db.models.signals import post_save
from django.db.models import Q,Sum
from shopback import paramconfig as pcfg
from shopback.archives.models import Supplier,PurchaseType,Deposite
from shopback.categorys.models import ProductCategory
from shopback.items.models import Product,ProductSku
from auth.utils import format_date
from utils import update_model_feilds

PURCHASE_STATUS = (
    (pcfg.PURCHASE_DRAFT,'草稿'),
    (pcfg.PURCHASE_APPROVAL,'审核'),
    (pcfg.PURCHASE_FINISH,'完成'),
    (pcfg.PURCHASE_INVALID,'作废'),
    (pcfg.PURCHASE_CLOSE,'关闭'),
)

PURCHASE_ITEM_STATUS = (
    (pcfg.PURCHASE_DRAFT,'草稿'),
    (pcfg.PURCHASE_APPROVAL,'审核'),
    (pcfg.PURCHASE_RETURN,'退货中'),
    (pcfg.PURCHASE_CLOSE,'退货关闭'),
    (pcfg.PURCHASE_FINISH,'完成'),
    (pcfg.PURCHASE_INVALID,'作废'),
    (pcfg.PURCHASE_REWORD,'返修'),
    (pcfg.PURCHASE_REWORDOVER,'返修结束'),
)

PURCHASE_ARRIVAL_STATUS = (
    (pcfg.PD_UNARRIVAL,'未到货'),
    (pcfg.PD_PARTARRIVAL,'部分到货'),
    (pcfg.PD_FULLARRIVAL,'全部到货'),
)

PURCHASE_STORAGE_STATUS = (
    (pcfg.PURCHASE_DRAFT,'草稿'),
    (pcfg.PURCHASE_APPROVAL,'验收'),
    (pcfg.PURCHASE_FINISH,'结算'),
    (pcfg.PURCHASE_INVALID,'作废'),
)

PURCHASE_PAYMENT_TYPE = (
    (pcfg.PC_COD_TYPE,'货到付款'),
    (pcfg.PC_PREPAID_TYPE,'预付款'),
    (pcfg.PC_POD_TYPE,'付款提货'),
    (pcfg.PC_OTHER_TYPE,'其它'),
)

PRODUCT_STATUS = (
    (pcfg.NORMAL,'有效'),
    (pcfg.DELETE,'作废'),
)


class Purchase(models.Model):
    """ 采购合同 """
    
    origin_no  = models.CharField(max_length=32,db_index=True,blank=True,verbose_name='原合同号')
    
    supplier     = models.ForeignKey(Supplier,null=True,blank=True,related_name='purchases',verbose_name='供应商')
    deposite     = models.ForeignKey(Deposite,null=True,blank=True,related_name='purchases',verbose_name='仓库')
    purchase_type = models.ForeignKey(PurchaseType,null=True,blank=True,related_name='purchases',verbose_name='采购类型')
    
    forecast_date = models.DateField(null=True,blank=True,verbose_name='预测到货日期')
    post_date     = models.DateField(null=True,blank=True,verbose_name='发货日期')
    service_date  = models.DateField(null=True,blank=True,verbose_name='业务日期')
    
    created      = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='创建日期')
    modified     = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='修改日期')
    
    total_fee    = models.FloatField(default=0.0,verbose_name='总费用')
    payment      = models.FloatField(default=0.0,verbose_name='实付')
    
    receiver_name = models.CharField(max_length=32,blank=True,verbose_name='收货人')
    
    status       = models.CharField(max_length=32,db_index=True,choices=PURCHASE_STATUS,
                                    default=pcfg.PURCHASE_DRAFT,verbose_name='订单状态')
    
    arrival_status    = models.CharField(max_length=20,db_index=True,choices=PURCHASE_ARRIVAL_STATUS,
                                    default=pcfg.PD_UNARRIVAL,verbose_name='到货状态')
    
    extra_name   = models.CharField(max_length=256,blank=True,verbose_name='标题')
    extra_info   = models.TextField(blank=True,verbose_name='备注')

    #attach_files 关联文件
    class Meta:
        db_table = 'shop_purchases_purchase'
        verbose_name=u'采购单'

    def __unicode__(self):
        return '<%s,%s,%s>'%(str(self.id),self.origin_no,self.extra_name)
    
    def gen_csv_tuple(self):
        
        pcsv = []
        pcsv.append((u'采购编号',str(self.id),u'采购标题',self.extra_name,u'供应商',self.supplier.supplier_name))
        pcsv.append((u'采购日期',format_date(self.service_date),u'预测到货日期',format_date(self.forecast_date)))
        pcsv.append((u'总费用',str(self.total_fee),u'实付',str(self.payment)))
        pcsv.append(('',''))
        
        pcsv.append((u'商品编码',u'商品名称',u'规格编码',u'规格名称',u'采购价',u'采购数量'))
        for item in self.purchase_items.exclude(status__in=(pcfg.PURCHASE_CLOSE,pcfg.PURCHASE_INVALID)).order_by('outer_id'):
            pcsv.append((item.outer_id,
                         item.name,
                         item.outer_sku_id,
                         item.properties_name,
                         str(item.price),
                         str(item.purchase_num)))
            
        return pcsv  
    
class PurchaseItem(models.Model):
    """ 采购项目 """
    
    purchase     = models.ForeignKey(Purchase,related_name='purchase_items',verbose_name='采购单')
    supplier_item_id = models.CharField(max_length=64,blank=True,verbose_name='供应商货号')
    
    outer_id     = models.CharField(max_length=32,null=False,blank=True,verbose_name='商品编码')
    name         = models.CharField(max_length=64,null=False,blank=True,verbose_name='商品名称')
    outer_sku_id     = models.CharField(max_length=32,null=False,blank=True,verbose_name='规格编码')
    properties_name  = models.CharField(max_length=64,null=False,blank=True,verbose_name='规格属性')
    
    purchase_num = models.IntegerField(null=True,default=0,verbose_name='采购数量')
    discount     = models.FloatField(null=True,default=0,verbose_name='折扣')
    
    std_price    = models.FloatField(default=0.0,verbose_name='标准进价')
    price        = models.FloatField(default=0.0,verbose_name='实际进价')
    
    total_fee    = models.FloatField(default=0.0,verbose_name='标准费用')
    payment      = models.FloatField(default=0.0,verbose_name='实付')
    
    created      = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='创建日期')
    modified     = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='修改日期')
    
    status       = models.CharField(max_length=32,db_index=True,choices=PURCHASE_ITEM_STATUS,
                                    default=pcfg.PURCHASE_DRAFT,verbose_name='状态')
    
    arrival_status    = models.CharField(max_length=20,db_index=True,choices=PURCHASE_ARRIVAL_STATUS,
                                    default=pcfg.PD_UNARRIVAL,verbose_name='到货状态')
    
    extra_info   = models.CharField(max_length=1000,blank=True,verbose_name='备注')
    
    class Meta:
        db_table = 'shop_purchases_item'
        unique_together = ("purchase","outer_id", "outer_sku_id")
        verbose_name='采购项目'
    
    def __unicode__(self):
        return 'CGZD%d'%self.id
 
 
def update_purchase_info(sender,instance,*args,**kwargs):
    """ 更新采购单信息 """
    
    instance.total_fee = int(instance.purchase_num or 0)*float(instance.std_price or 0)
    instance.payment   = int(instance.purchase_num or 0)*float(instance.price or 0)
    update_model_feilds(instance,update_fields=['total_fee','payment'])
    
    purchase = instance.purchase
    purchase_items = instance.purchase.purchase_items.exclude(status=pcfg.PURCHASE_INVALID)
    if purchase.status in (pcfg.PURCHASE_DRAFT,pcfg.PURCHASE_APPROVAL):
        purchase.total_fee = purchase_items.aggregate(total_fees=Sum('total_fee'))['total_fees'] or 0
        purchase.payment   = purchase_items.aggregate(total_payment=Sum('payment'))['total_payment'] or 0
    
    if purchase_items.count() >0:
        if purchase_items.exclude(arrival_status=pcfg.PD_UNARRIVAL).count()==0:
            purchase.arrival_status = pcfg.PD_UNARRIVAL
        elif purchase_items.filter(arrival_status=pcfg.PD_PARTARRIVAL).count()>0:
            purchase.arrival_status = pcfg.PD_PARTARRIVAL
        elif purchase_items.exclude(arrival_status=pcfg.PD_FULLARRIVAL).count()==0:
            purchase.arrival_status = pcfg.PD_FULLARRIVAL
    
        if purchase_items.exclude(status=pcfg.PURCHASE_CLOSE).count()==0:
            purchase.status=pcfg.PURCHASE_CLOSE
    
    update_model_feilds(purchase,update_fields=['total_fee','payment','arrival_status','status'])
        
post_save.connect(update_purchase_info, sender=PurchaseItem)
    
    
class PurchaseStorage(models.Model):
    """ 采购入库单 """
    
    purchase      = models.ForeignKey(Purchase,related_name='purchase_storages',verbose_name='采购单')
    origin_no     = models.CharField(max_length=256,db_index=True,blank=True,verbose_name='原单据号')
    purchase_no   = models.CharField(max_length=256,db_index=True,blank=True,verbose_name='采购单号')
    
    supplier      = models.ForeignKey(Supplier,null=True,blank=True,related_name='purchase_storages',verbose_name='供应商')
    deposite      = models.ForeignKey(Deposite,null=True,blank=True,related_name='purchases_storages',verbose_name='仓库')
    purchase_type = models.ForeignKey(PurchaseType,null=True,blank=True,related_name='purchases_storages',verbose_name='采购类型')
    
    forecast_date = models.DateTimeField(null=True,blank=True,verbose_name='预计到货日期')
    post_date     = models.DateTimeField(null=True,blank=True,verbose_name='实际到货日期')

    created      = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='创建日期')
    modified     = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='修改日期')
    
    status       = models.CharField(max_length=32,db_index=True,choices=PURCHASE_STORAGE_STATUS,
                                    default=pcfg.PURCHASE_DRAFT,verbose_name='状态')
    
    logistic_company = models.CharField(max_length=64,blank=True,verbose_name='物流公司')
    out_sid          = models.CharField(max_length=64,db_index=True,blank=True,verbose_name='物流编号')
    
    extra_name  = models.CharField(max_length=256,blank=True,verbose_name='标题')
    extra_info  = models.TextField(blank=True,verbose_name='备注')
    
    class Meta:
        db_table     = 'shop_purchases_storage'
        verbose_name = '采购入库单'

    def __unicode__(self):
        return 'RKD%d'%self.id
     

class PurchaseStorageItem(models.Model):
    """ 采购入库项目 """
    
    purchase_storage     = models.ForeignKey(PurchaseStorage,related_name='purchase_storage_items',verbose_name='入库单')
    supplier_item_id     = models.CharField(max_length=64,blank=True,verbose_name='供应商货号')
    
    outer_id     = models.CharField(max_length=32,null=False,blank=True,verbose_name='商品编码')
    name         = models.CharField(max_length=64,null=False,blank=True,verbose_name='商品名称')
    outer_sku_id     = models.CharField(max_length=32,null=False,blank=True,verbose_name='规格编码')
    properties_name  = models.CharField(max_length=64,null=False,blank=True,verbose_name='规格属性')
    
    storage_num  = models.IntegerField(null=True,default=0,verbose_name='入库数量')
    
    created      = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='创建日期')
    modified     = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='修改日期')
    
    status       = models.CharField(max_length=32,db_index=True,choices=PRODUCT_STATUS,
                                    default=pcfg.NORMAL,verbose_name='状态')
    
    extra_info   = models.CharField(max_length=1000,blank=True,verbose_name='备注')
    
    class Meta:
        db_table = 'shop_purchases_storageitem'
        unique_together = ("purchase_storage","outer_id", "outer_sku_id")
        verbose_name = '采购入库项目'
    
    def __unicode__(self):
        return 'RKZD%d'%self.id
    
    

class PurchasePaymentItem(models.Model):
    """ 
        采购付款项目：
        1,货到付款
        2,预付款
        3,付款提货
    """    
    
    purchase  = models.ForeignKey(Purchase,null=True,related_name='purchase_payment',verbose_name='采购合同')
    
    storage   = models.ForeignKey(PurchaseStorage,null=True,related_name='purchase_payment',verbose_name='入库单')
    
    pay_type  = models.CharField(max_length=4,db_index=True,choices=PURCHASE_PAYMENT_TYPE,verbose_name='付款类型')
    
    pay_time     = models.DateTimeField(null=True,blank=True,verbose_name='付款日期')
    
    payment   = models.FloatField(default=0,verbose_name='付款金额')
    
    status       = models.CharField(max_length=32,db_index=True,verbose_name='状态')
    
    extra_info   = models.TextField(max_length=1000,blank=True,verbose_name='备注')
    
    class Meta:
        db_table = 'shop_purchases_payment_item'
        verbose_name='采购付款项目'
    
    def __unicode__(self):
        return '<%s,%s,%s>'%(str(self.purchase),str(self.storage),str(self.payment))
    
    