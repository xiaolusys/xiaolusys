#-*- coding:utf8 -*-
from django.db import models
from django.db.models.signals import post_save,post_delete
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
)


PURCHASE_ARRIVAL_STATUS = (
    (pcfg.PD_UNARRIVAL,'未到货'),
    (pcfg.PD_PARTARRIVAL,'部分到货'),
    (pcfg.PD_FULLARRIVAL,'全部到货'),
)

PURCHASE_STORAGE_STATUS = (
    (pcfg.PURCHASE_DRAFT,'草稿'),
    (pcfg.PURCHASE_APPROVAL,'审核'),
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
    
    purchase_num = models.IntegerField(null=True,default=0,verbose_name='采购数量')
    storage_num  = models.IntegerField(null=True,default=0,verbose_name='已入库数')
    
    total_fee    = models.FloatField(default=0.0,verbose_name='总费用')
    payment      = models.FloatField(default=0.0,verbose_name='已付')
    
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
        verbose_name = u'采购单'
        verbose_name_plural = u'采购单列表'
        permissions = [
                       ("can_purchase_check", u"审批采购合同"),
                       ("can_purchase_confirm", u"确认采购完成"),
                       ]

    def __unicode__(self):
        return '<%s,%s,%s>'%(str(self.id),self.origin_no,self.extra_name)
    
    @property
    def effect_purchase_items(self):
        return self.purchase_items.filter(status=pcfg.NORMAL)
    
    @property
    def unfinish_purchase_items(self):
        return self.effect_purchase_items.filter(arrival_status__in=(pcfg.PD_UNARRIVAL,pcfg.PD_PARTARRIVAL))
        
    def gen_csv_tuple(self):
        
        pcsv = []
        pcsv.append((u'采购编号',str(self.id),u'采购标题',self.extra_name,u'供应商',self.supplier and self.supplier.supplier_name or ''))
        pcsv.append((u'采购日期',self.service_date and format_date(self.service_date) or '',
                     u'预测到货日期',self.forecast_date and format_date(self.forecast_date)) or '')
        pcsv.append((u'总费用',str(self.total_fee),u'实付',str(self.payment)))
        pcsv.append(('',''))
        
        pcsv.append((u'商品编码',u'商品名称',u'规格编码',u'规格名称',u'采购价',u'采购数量'))
        for item in self.effect_purchase_items.order_by('outer_id'):
            pcsv.append((item.outer_id,
                         item.name,
                         item.outer_sku_id,
                         item.properties_name,
                         str(item.price),
                         str(item.purchase_num)))
            
        return pcsv
      
    @property
    def json(self):
        """ 获取采购单JSON信息 """
        
        purchase_items = []
        for item in self.effect_purchase_items:
            purchase_items.append(item.json)
        
        return {
                'id':self.id,
                'origin_no':self.origin_no,
                'supplier_id':self.supplier and self.supplier.id or '',
                'deposite_id':self.deposite and self.deposite.id or '',
                'purchase_type_id':self.purchase_type and self.purchase_type.id or '',
                'forecast_date':self.forecast_date,
                'post_date':self.post_date,
                'service_date':self.service_date,
                'total_fee':self.total_fee,
                'payment':self.payment,
                'extra_name':self.extra_name,
                'extra_info':self.extra_info,
                'purchase_items':purchase_items
                }
    
        
    def get_ship_storages(self):
        """ 获取关联入库信息 """
        storage_map    = {}
        relate_ship  = PurchaseStorageRelationship.objects.filter(purchase_id=self.id)
        for ship in relate_ship:
            
            storage_id      = ship.storage_id
            storage_item_id = ship.storage_item_id
            
            storage      = PurchaseStorage.objects.get(id=storage_id)
            storage_item = PurchaseStorageItem.objects.get(id=storage_item_id)
                
            if storage_map.has_key(storage_id):
                storage_map[storage_id]['storage_items'].append({
                                                               'id':storage_item.id,
                                                               'outer_id':storage_item.outer_id,
                                                               'name':storage_item.name,
                                                               'outer_sku_id':storage_item.outer_sku_id,
                                                               'properties_name':storage_item.properties_name,
                                                               'storage_num':storage_item.storage_num,
                                                               'payment':ship.relate_fee,
                                                               'ship_num':ship.storage_num,
                                                               'status':dict(PRODUCT_STATUS).get(storage_item.status)})
                
            else:
                storage_map[storage_id] ={
                                            'id':storage.id,
                                            'origin_no':storage.origin_no,
                                            'extra_name':storage.extra_name,
                                            'supplier_name':storage.supplier and storage.supplier.supplier_name or '',
                                            'logistic_company':storage.logistic_company,
                                            'out_sid':storage.out_sid,
                                            'status':dict(PURCHASE_STORAGE_STATUS).get(storage.status),
                                            'storage_items':[{'id':storage_item.id,
                                                               'outer_id':storage_item.outer_id,
                                                               'name':storage_item.name,
                                                               'outer_sku_id':storage_item.outer_sku_id,
                                                               'properties_name':storage_item.properties_name,
                                                               'storage_num':storage_item.storage_num,
                                                               'payment':ship.relate_fee,
                                                               'ship_num':ship.storage_num,
                                                               'status':dict(PRODUCT_STATUS).get(storage_item.status)}]
                                            }
        return [v for k,v in storage_map.iteritems()]    
        
        
        
class PurchaseItem(models.Model):
    """ 采购项目 """
    
    purchase     = models.ForeignKey(Purchase,related_name='purchase_items',verbose_name='采购单')
    supplier_item_id = models.CharField(max_length=64,blank=True,verbose_name='供应商货号')
    
    outer_id     = models.CharField(max_length=32,null=False,blank=True,verbose_name='商品编码')
    name         = models.CharField(max_length=64,null=False,blank=True,verbose_name='商品名称')
    outer_sku_id     = models.CharField(max_length=32,null=False,blank=True,verbose_name='规格编码')
    properties_name  = models.CharField(max_length=64,null=False,blank=True,verbose_name='规格属性')
    
    purchase_num = models.IntegerField(null=True,default=0,verbose_name='采购数量')
    storage_num  = models.IntegerField(null=True,default=0,verbose_name='已入库数')
    
    discount     = models.FloatField(null=True,default=0,verbose_name='折扣')
    std_price    = models.FloatField(default=0.0,verbose_name='标准进价')
    price        = models.FloatField(default=0.0,verbose_name='实际进价')
    
    total_fee    = models.FloatField(default=0.0,verbose_name='总费用')
    payment      = models.FloatField(default=0.0,verbose_name='已付')

    created      = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='创建日期')
    modified     = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='修改日期')
    
    status       = models.CharField(max_length=32,db_index=True,choices=PRODUCT_STATUS,
                                    default=pcfg.NORMAL,verbose_name='状态')
    
    arrival_status    = models.CharField(max_length=20,db_index=True,choices=PURCHASE_ARRIVAL_STATUS,
                                    default=pcfg.PD_UNARRIVAL,verbose_name='到货状态')
    
    extra_info   = models.CharField(max_length=1000,blank=True,verbose_name='备注')
    
    class Meta:
        db_table = 'shop_purchases_item'
        unique_together = ("purchase","outer_id", "outer_sku_id")
        verbose_name = u'采购项目'
        verbose_name_plural = u'采购项目列表'
        permissions = [
                       ("can_storage_confirm", u"确认入库数量"),
                       ]
    
    def __unicode__(self):
        return 'CGZD%d'%self.id
    
    @property
    def json(self):
        """ 获取采购项JSON信息 """
   
        return {
                'id':self.id,
                'supplier_item_id':self.supplier_item_id,
                'outer_id':self.outer_id,
                'name':self.name,
                'outer_sku_id':self.outer_sku_id,
                'properties_name':self.properties_name,
                'total_fee':self.total_fee,
                'payment':self.payment,
                'purchase_num':self.purchase_num,
                'price':self.price,
                'std_price':self.std_price,
                }
 
 
def update_purchase_info(sender,instance,*args,**kwargs):
    """ 更新采购单信息 """
    
    purchase = instance.purchase
    purchase_items = instance.purchase.effect_purchase_items
    
    purchase.total_fee = purchase_items.aggregate(total_fees=Sum('total_fee'))['total_fees'] or 0
    purchase.payment   = purchase_items.aggregate(total_payment=Sum('payment'))['total_payment'] or 0
    purchase.purchase_num  = purchase_items.aggregate(total_purchase_num=Sum('purchase_num'))['total_purchase_num'] or 0
    purchase.storage_num   = purchase_items.aggregate(total_storage_num=Sum('storage_num'))['total_storage_num'] or 0
    
    if purchase_items.count() >0:
        if purchase_items.exclude(arrival_status=pcfg.PD_UNARRIVAL).count()==0:
            purchase.arrival_status = pcfg.PD_UNARRIVAL
        elif purchase_items.filter(arrival_status=pcfg.PD_PARTARRIVAL).count()>0:
            purchase.arrival_status = pcfg.PD_PARTARRIVAL
        elif purchase_items.exclude(arrival_status=pcfg.PD_FULLARRIVAL).count()==0:
            purchase.arrival_status = pcfg.PD_FULLARRIVAL
    
        if purchase_items.exclude(status=pcfg.PURCHASE_CLOSE).count()==0:
            purchase.status=pcfg.PURCHASE_CLOSE
    
    update_model_feilds(purchase,update_fields=['total_fee','payment','arrival_status','status','purchase_num','storage_num'])
        
post_save.connect(update_purchase_info, sender=PurchaseItem)
    
    
class PurchaseStorage(models.Model):
    """ 采购入库单 """
    
    origin_no     = models.CharField(max_length=256,db_index=True,blank=True,verbose_name='原单据号')
    
    supplier      = models.ForeignKey(Supplier,null=True,blank=True,related_name='purchase_storages',verbose_name='供应商')
    deposite      = models.ForeignKey(Deposite,null=True,blank=True,related_name='purchases_storages',verbose_name='仓库')
    
    forecast_date = models.DateField(null=True,blank=True,verbose_name='预计到货日期')
    post_date     = models.DateField(null=True,db_index=True,blank=True,verbose_name='实际到货日期')

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
        verbose_name = u'采购入库单'
        verbose_name_plural = u'采购入库单列表'

    def __unicode__(self):
        return 'RKD%d'%self.id
    
    @property
    def normal_storage_items(self):
        return self.purchase_storage_items.filter(status=pcfg.NORMAL)
    
    def gen_csv_tuple(self):
        
        pcsv = []
        pcsv.append((u'入库单号',str(self.id),u'入库标题',self.extra_name,u'供应商',self.supplier and self.supplier.supplier_name or ''))
        pcsv.append((u'预测到货日期',self.forecast_date and format_date(self.forecast_date),
                     u'实际到货日期',self.post_date and format_date(self.post_date)))
        pcsv.append(('',''))
        
        pcsv.append((u'商品编码',u'商品名称',u'规格编码',u'规格名称',u'入库数量'))
        for item in self.purchase_storage_items.exclude(status__in=(pcfg.PURCHASE_CLOSE,pcfg.PURCHASE_INVALID)).order_by('outer_id'):
            pcsv.append((item.outer_id,
                         item.name,
                         item.outer_sku_id,
                         item.properties_name,
                         str(item.storage_num)))
            
        return pcsv 
    
    @property
    def json(self):
        """ 获取入库单JSON信息 """
        
        purchase_items = []
        for item in self.normal_storage_items:
            purchase_items.append(item.json)
        
        return {
                'id':self.id,
                'origin_no':self.origin_no,
                'supplier_id':self.supplier and self.supplier.id or '',
                'deposite_id':self.deposite and self.deposite.id or '',
                'forecast_date':self.forecast_date,
                'post_date':self.post_date,
                'logistic_company':self.logistic_company,
                'out_sid':self.out_sid,
                'extra_name':self.extra_name,
                'extra_info':self.extra_info,
                'purchase_storage_items':purchase_items,
                }
        
        
    def distribute_storage_num(self):
        """ 分配入库项数量到采购单,返回未分配的采购项 """
        
        unmatch_storage_items     = []
        uncomplete_purchase = Purchase.objects.filter(supplier=self.supplier,
                                                      status=pcfg.PURCHASE_APPROVAL).order_by('service_date')
        
        for storage_item in self.normal_storage_items:
            storage_ships = PurchaseStorageRelationship.objects.filter(
                            storage_id=self.id,storage_item_id=storage_item.id)
            
            undist_storage_num = storage_item.storage_num - (storage_ships.aggregate(
                                        dist_storage_num=Sum('storage_num')).get('dist_storage_num') or 0) #未分配库存数
            if undist_storage_num>0:
                outer_id     = storage_item.outer_id
                outer_sku_id = storage_item.outer_sku_id
                purchase_item  = None
                purchase_items = []

                for purchase in uncomplete_purchase:
                    try:
                        purchase_item = PurchaseItem.objects.get(
                                    purchase=purchase,outer_id=outer_id,outer_sku_id=outer_sku_id)
                    except PurchaseItem.DoesNotExist:
                        purchase_item = None
                    else:
                        purchase_items.append(purchase_item)
                
                for purchase_item in purchase_items:
                    diff_num = purchase_item.purchase_num-purchase_item.storage_num #采购项剩余未到货数
                    if diff_num >0:
                        storage_ship,state    = PurchaseStorageRelationship.objects.get_or_create(
                                                           purchase_id=purchase_item.purchase.id,
                                                           purchase_item_id=purchase_item.id,
                                                           storage_id=self.id,
                                                           storage_item_id=storage_item.id)
                        storage_ship.outer_id     = outer_id
                        storage_ship.outer_sku_id = outer_sku_id
                        
                        diff_num  = min(diff_num,undist_storage_num)
                        storage_ship.storage_num  = diff_num
                        storage_ship.save()
                    
                    undist_storage_num = undist_storage_num - diff_num    
                    #如果  未分配库存数 小于等于  采购项剩余未到货数,分配后退出循环
                    if undist_storage_num<=0: 
                        break
        
                if undist_storage_num>0:
                    storage_item_json = storage_item.json
                    storage_item_json['undist_storage_num'] = undist_storage_num
                    unmatch_storage_items.append(storage_item_json)
        
        return unmatch_storage_items
        
        
    def get_ship_purchases(self):
        """ 获取关联采购信息 """
        purchase_map    = {}
        relate_ship  = PurchaseStorageRelationship.objects.filter(storage_id=self.id)
        for ship in relate_ship:
            
            purchase_id      = ship.purchase_id
            purchase_item_id = ship.purchase_item_id
            
            purchase      = Purchase.objects.get(id=purchase_id)
            purchase_item = PurchaseItem.objects.get(id=purchase_item_id)
                
            if purchase_map.has_key(purchase_id):
                purchase_map[purchase_id]['purchase_items'].append({
                                                               'id':purchase_item.id,
                                                               'outer_id':purchase_item.outer_id,
                                                               'name':purchase_item.name,
                                                               'outer_sku_id':purchase_item.outer_sku_id,
                                                               'properties_name':purchase_item.properties_name,
                                                               'purchase_num':purchase_item.purchase_num,
                                                               'storage_num':purchase_item.storage_num,
                                                               'ship_num':ship.storage_num,
                                                               'arrival_status':dict(PURCHASE_ARRIVAL_STATUS).get(purchase_item.arrival_status),
                                                               'status':dict(PRODUCT_STATUS).get(purchase_item.status)})
                
            else:
                purchase_map[purchase_id] ={
                                            'id':purchase.id,
                                            'origin_no':purchase.origin_no,
                                            'extra_name':purchase.extra_name,
                                            'supplier_name':purchase.supplier and purchase.supplier.supplier_name or '未填写',
                                            'service_date':purchase.service_date,
                                            'purchase_num':purchase.purchase_num,
                                            'storage_num':purchase.storage_num,
                                            'arrival_status':dict(PURCHASE_ARRIVAL_STATUS).get(purchase.arrival_status),
                                            'status':dict(PURCHASE_STATUS).get(purchase.status),
                                            'purchase_items':[{'id':purchase_item.id,
                                                               'outer_id':purchase_item.outer_id,
                                                               'name':purchase_item.name,
                                                               'outer_sku_id':purchase_item.outer_sku_id,
                                                               'properties_name':purchase_item.properties_name,
                                                               'purchase_num':purchase_item.purchase_num,
                                                               'storage_num':purchase_item.storage_num,
                                                               'ship_num':ship.storage_num,
                                                               'arrival_status':dict(PURCHASE_ARRIVAL_STATUS).get(purchase_item.arrival_status),
                                                               'status':dict(PRODUCT_STATUS).get(purchase_item.status)}]
                                            }
        return [v for k,v in purchase_map.iteritems()]    
            
            
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
        verbose_name = u'采购入库项目'
        verbose_name_plural = u'采购入库项目列表'
    
    def __unicode__(self):
        return '%s'(self.id and str(self.id) or 'empty')
    
    @property
    def json(self):
        """ 获取入库项JSON信息 """
        return {
                'id':self.id,
                'supplier_item_id':self.supplier_item_id,
                'outer_id':self.outer_id,
                'name':self.name,
                'outer_sku_id':self.outer_sku_id,
                'properties_name':self.properties_name,
                'storage_num':self.storage_num,
                }
        
    
class PurchaseStorageRelationship(models.Model):
    """ 采购与入库商品项目关联 """
    
    purchase_id       =  models.IntegerField(verbose_name='采购单ID')
    purchase_item_id  =  models.IntegerField(verbose_name='采购项目ID')
    storage_id        =  models.IntegerField(db_index=True,verbose_name='入库单ID')
    storage_item_id   =  models.IntegerField(verbose_name='入库项目ID')
    
    outer_id          = models.CharField(max_length=32,verbose_name='商品编码')
    outer_sku_id      = models.CharField(max_length=32,null=False,blank=True,verbose_name='规格编码')
    
    is_addon          = models.BooleanField(default=False,verbose_name='更新商品库存')
    storage_num       = models.IntegerField(null=True,default=0,verbose_name='关联入库数量')
    relate_fee        = models.FloatField(default=0.0,verbose_name='支付费用')
    
    class Meta:
        db_table = 'shop_purchases_relationship'
        unique_together = (("purchase_id","purchase_item_id","storage_id","storage_item_id"),)
        verbose_name = u'采购入库关联'
        verbose_name_plural = u'采购入库关联'
    
    def __unicode__(self):
        return 'RKZD%d'%self.id
    
    
def update_purchaseitem_storage_and_fee(sender,instance,*args,**kwargs):
    """ 更新采购单项目信息 """
    
    purchase_item = PurchaseItem.objects.get(id=instance.purchase_item_id)
    
    relation_dict = PurchaseStorageRelationship.objects.filter(
        purchase_id=instance.purchase_id,purchase_item_id=instance.purchase_item_id)\
        .aggregate(total_storage_num=Sum('storage_num'),total_relate_fee=Sum('relate_fee'))
        
    total_storage_num = relation_dict.get('total_storage_num') or 0
    taotao_payment    = relation_dict.get('total_relate_fee') or 0
    
    purchase_item.arrival_status = total_storage_num<=0 and pcfg.PD_UNARRIVAL or \
        (total_storage_num>=purchase_item.purchase_num and pcfg.PD_FULLARRIVAL or pcfg.PD_PARTARRIVAL)
    purchase_item.storage_num = total_storage_num
    purchase_item.payment     = taotao_payment
    purchase_item.save()
 
#修改，删除采购入库关联项时，应更新其对应的采购项信息       
post_save.connect(update_purchaseitem_storage_and_fee, sender=PurchaseStorageRelationship)
    
post_delete.connect(update_purchaseitem_storage_and_fee, sender=PurchaseStorageRelationship)


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
        verbose_name=u'采购付款项目'
        verbose_name_plural = u'采购付款项目列表'
    
    def __unicode__(self):
        return '<%s,%s,%s>'%(str(self.purchase),str(self.storage),str(self.payment))
    
    