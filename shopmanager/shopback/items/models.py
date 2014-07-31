#-*- coding:utf-8 -*-
"""
淘宝普通平台模型:
Product:系统内部商品，唯一对应多家店铺的商品外部编码,
ProductSku:淘宝平台商品sku，
Item:淘宝平台商品，
"""
import json
import datetime
from django.db import models
from django.db.models import Sum,Avg,F
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField
from shopback.categorys.models import Category,ProductCategory
from shopback.archives.models import Deposite,DepositeDistrict
from shopback import paramconfig as pcfg
from django.db.models.signals import post_save
from shopback.users.models import User
from .managers import ProductManager
from auth import apis
from common.utils import update_model_fields
import logging

logger  = logging.getLogger('django.request')

APPROVE_STATUS  = (
    (pcfg.ONSALE_STATUS,u'在售'),
    (pcfg.INSTOCK_STATUS,u'库中'),
)

ONLINE_PRODUCT_STATUS = (
    (pcfg.NORMAL,u'使用'),
    (pcfg.REMAIN,u'待用'),
    (pcfg.DELETE,u'作废'),
)

PRODUCT_STATUS = (
    (pcfg.NORMAL,u'使用'),
    (pcfg.DELETE,u'作废'),
)

class ProductDefectException(Exception):
    pass

class Product(models.Model):
    """ 系统商品（根据淘宝外部编码) """
    
    ProductCodeDefect = ProductDefectException
    PRODUCT_CODE_DELIMITER = '.'
    
    outer_id     = models.CharField(max_length=64,unique=True,null=False,
                                    blank=True,verbose_name=u'外部编码')
    name         = models.CharField(max_length=64,blank=True,verbose_name=u'商品名称')
    
    barcode      = models.CharField(max_length=64,blank=True,db_index=True,verbose_name=u'条码')
    category     = models.ForeignKey(ProductCategory,null=True,blank=True,
                                     related_name='products',verbose_name=u'内部分类')
    pic_path     = models.CharField(max_length=256,blank=True)
    
    collect_num  = models.IntegerField(default=0,verbose_name=u'库存数')  #库存数
    warn_num     = models.IntegerField(null=True,default=0,verbose_name=u'警告数')    #警戒库位
    remain_num   = models.IntegerField(null=True,default=0,verbose_name=u'预留数')    #预留库存
    wait_post_num   = models.IntegerField(null=True,default=0,verbose_name=u'待发数') #待发数
    reduce_num   = models.IntegerField(null=True,default=0,verbose_name=u'预减数')    #下次入库减掉这部分库存
    
    cost         = models.FloatField(default=0,verbose_name=u'成本价')
    std_purchase_price = models.FloatField(default=0,verbose_name=u'标准进价')
    std_sale_price     = models.FloatField(default=0,verbose_name=u'吊牌价')
    agent_price        = models.FloatField(default=0,verbose_name=u'代理售价')
    staff_price        = models.FloatField(default=0,verbose_name=u'员工价')
    
    weight       = models.CharField(max_length=10,blank=True,verbose_name=u'重量(g)')
    
    created      = models.DateTimeField(null=True,blank=True,
                                        auto_now_add=True,verbose_name=u'创建时间')
    modified     = models.DateTimeField(null=True,blank=True,
                                        auto_now=True,verbose_name=u'修改时间')
    
    is_split   = models.BooleanField(default=False,verbose_name=u'需拆分')
    is_match   = models.BooleanField(default=False,verbose_name=u'有匹配')
    
    sync_stock   = models.BooleanField(default=True,verbose_name=u'库存同步')
    is_assign    = models.BooleanField(default=False,verbose_name=u'取消警告') 
    
    post_check   = models.BooleanField(default=False,verbose_name=u'需扫描')
    status       = models.CharField(max_length=16,db_index=True,
                                    choices=ONLINE_PRODUCT_STATUS,
                                    default=pcfg.NORMAL,verbose_name=u'商品状态')
    
    match_reason = models.CharField(max_length=80,blank=True,verbose_name=u'匹配原因')
    buyer_prompt = models.CharField(max_length=60,blank=True,verbose_name=u'客户提示')
    memo         = models.TextField(max_length=1000,blank=True,verbose_name=u'备注')
    
    objects = ProductManager()
    
    class Meta:
        db_table = 'shop_items_product'
        verbose_name = u'库存商品'
        verbose_name_plural = u'库存商品列表'
        permissions = [
                       ("change_product_skunum", u"修改库存信息"),
                       ]
    
    def __unicode__(self):
        return '<%s,%s>'%(self.outer_id,self.name)
    
    @property
    def eskus(self):
        return self.prod_skus.filter(status=pcfg.NORMAL)
    
    @property
    def pskus(self):
        return self.prod_skus.filter(status__in=(pcfg.NORMAL,pcfg.REMAIN))
    
    @property
    def BARCODE(self):
        return self.barcode.strip() or self.outer_id.strip()
    
    @property
    def realnum(self):
        return self.collect_num - self.wait_post_num
    
    @property
    def is_out_stock(self):
        if self.collect_num<0 or self.wait_post_num <0 :
            self.collect_num = self.collect_num >0 and self.collect_num or 0 
            self.wait_post_num = self.wait_post_num >0 and self.wait_post_num or 0 
            self.save()
        return self.collect_num-self.wait_post_num <= 0
    
    @property
    def json(self):
        
        skus_json = []
        for sku in self.pskus:
            skus_json.append(sku.json)
        
        return {
                'id':self.id,
                'outer_id':self.outer_id,
                'name':self.name,
                'collect_num':self.collect_num,
                'remain_num':self.remain_num,
                'warn_num':self.warn_num,
                'wait_post_num':self.wait_post_num,
                'cost':self.cost,
                'std_purchase_price':self.std_purchase_price,
                'std_sale_price':self.std_sale_price,
                'agent_price':self.agent_price,
                'staff_price':self.staff_price,
                'weight':self.weight,
                'sync_stock':self.sync_stock,
                'is_split':self.is_split,
                'is_match':self.is_match,
                'is_assign':self.is_assign,
                'is_stock_warn':self.is_stock_warn,
                'is_warning':self.is_warning,
                'post_check':self.post_check,
                'status':dict(ONLINE_PRODUCT_STATUS).get(self.status,''),
                'buyer_prompt':self.buyer_prompt,
                'memo':self.memo,
                'districts':self.get_district_list(),
                'barcode':self.BARCODE,
                'match_reason':self.match_reason,
                'skus':skus_json
                }    
        
    def update_collect_num(self,num,full_update=False,dec_update=False):
        """
            更新商品库存:
                full_update:是否全量更新
                dec_update:是否减库存
        """
        if full_update:
            self.collect_num = num
        elif dec_update:
            self.collect_num = F('collect_num') - num
        else:
            self.collect_num = F('collect_num') + num
        update_model_fields(self,update_fields=['collect_num'])
        
        self.collect_num = self.__class__.objects.get(id=self.id).collect_num
        
        
    def update_wait_post_num(self,num,full_update=False,dec_update=False):
        """
            更新商品待发数:
                full_update:是否全量更新
                dec_update:是否减库存
        """
        if full_update:
            self.wait_post_num = num
        elif dec_update:
            self.wait_post_num = F('wait_post_num') - num
        else:
            self.wait_post_num = F('wait_post_num') + num
        update_model_fields(self,update_fields=['wait_post_num'])
        
        self.wait_post_num = self.__class__.objects.get(id=self.id).wait_post_num
    
    def update_reduce_num(self,num,full_update=False,dec_update=False):
        """
            更新商品库存:
                full_update:是否全量更新
                dec_update:是否减库存
        """
        if full_update:
            self.reduce_num = num
        elif dec_update:
            self.reduce_num = F('reduce_num') - num
        else:
            self.reduce_num = F('reduce_num') + num
        update_model_fields(self,update_fields=['reduce_num'])
        
        self.reduce_num = self.__class__.objects.get(id=self.id).reduce_num
        
    
    def update_quantity_by_storage_num(self,num):
        
        if num < 0 :
            raise Exception(u'入库更新商品库存数不能小于0')
        
        if num > self.reduce_num:
            real_update_num = num - self.reduce_num
            real_reduct_num = 0
        else:
            real_update_num = 0
            real_reduct_num = self.reduce_num - num
            
        self.update_collect_num(real_update_num)
        self.update_reduce_num(real_reduct_num,full_update=True)
    
    @property
    def is_stock_warn(self):
        """
        库存是否警告
        """
        for sku in self.eskus:
            if sku.is_stock_warn and not sku.is_assign:
                return True   
            
        collect_num = self.collect_num >0 and self.collect_num or 0
        remain_num = self.remain_num >0 and self.remain_num or 0
        wait_post_num = self.wait_post_num >0 and self.wait_post_num or 0 
        
        sync_num = collect_num - remain_num - wait_post_num
        return sync_num <= 0
    
    @property
    def is_warning(self):
        """
        库存预警,昨天的销售大今天能同步的库存
        """
        for sku in self.eskus:
            if sku.is_warning:
                return True
            
        collect_num = self.collect_num >0 and self.collect_num or 0
        remain_num = self.remain_num >0 and self.remain_num or 0
        wait_post_num = self.wait_post_num >0 and self.wait_post_num or 0   
        sync_num = collect_num - remain_num - wait_post_num
        return self.warn_num >0 and self.warn_num >= sync_num
    
    def get_district_list(self):
        locations = ProductLocation.objects.filter(product_id=self.id)
        return [(l.district.parent_no,l.district.district_no) for l in locations]
    
    def get_districts_code(self):
        """ 商品库中区位 """
        locations = self.get_district_list()
        
        sdict = {}
        for d in locations:
            dno = d[1]
            pno = d[0]
            if sdict.has_key(pno):
                sdict[pno].add(dno)
            else:
                sdict[pno] = set([dno])
        ds = []
        for k,v in sdict.iteritems():
            ds.append(len(v)>1 and '%s-[%s]'%(k,','.join(list(v))) or '%s-%s'%(k,v.pop()))
        
        return ','.join(ds)
    
class ProductSku(models.Model):
    
    """ 
        抽象商品规格（根据淘宝规格外部编码），描述：
        1,映射淘宝出售商品规格与采购商品规格桥梁；
        2,库存管理的规格核心类；
    """
    
    outer_id = models.CharField(max_length=64,blank=False,verbose_name='规格外部编码')
    
    barcode  = models.CharField(max_length=64,blank=True,db_index=True,verbose_name='条码')
    product  = models.ForeignKey(Product,null=True,related_name='prod_skus',verbose_name='商品')
    
    quantity = models.IntegerField(default=0,verbose_name='库存数')
    warn_num     = models.IntegerField(null=True,default=0,verbose_name='警戒数')    #警戒库位
    remain_num   = models.IntegerField(null=True,default=0,verbose_name='预留数')    #预留库存
    wait_post_num = models.IntegerField(null=True,default=0,verbose_name='待发数')    #待发数
    reduce_num   = models.IntegerField(null=True,default=0,verbose_name='预减数')    #下次入库减掉这部分库存
    
    cost          = models.FloatField(default=0,verbose_name='成本价')
    std_purchase_price = models.FloatField(default=0,verbose_name='标准进价')
    std_sale_price     = models.FloatField(default=0,verbose_name='吊牌价')
    agent_price        = models.FloatField(default=0,verbose_name='代理售价')
    staff_price        = models.FloatField(default=0,verbose_name='员工价')
    
    weight             = models.CharField(max_length=10,blank=True,verbose_name='重量(g)')
    
    properties_name    = models.TextField(max_length=200,blank=True,verbose_name='线上规格名称')
    properties_alias   = models.TextField(max_length=200,blank=True,verbose_name='系统规格名称')
    
    is_split   = models.BooleanField(default=False,verbose_name='需拆分')
    is_match   = models.BooleanField(default=False,verbose_name='有匹配')
    
    sync_stock   = models.BooleanField(default=True,verbose_name='库存同步') 
    #是否手动分配库存，当库存充足时，系统自动设为False，手动分配过后，确定后置为True
    is_assign    = models.BooleanField(default=False,verbose_name='取消警告') 
    
    post_check   = models.BooleanField(default=False,verbose_name='需扫描')
    created      = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='创建时间')
    modified     = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='修改时间')
    status       = models.CharField(max_length=10,db_index=True,choices=ONLINE_PRODUCT_STATUS,
                                    default=pcfg.NORMAL,verbose_name='规格状态')  #normal,delete
    
    match_reason = models.CharField(max_length=80,blank=True,verbose_name='匹配原因')
    buyer_prompt = models.CharField(max_length=60,blank=True,verbose_name='客户提示')
    memo         = models.TextField(max_length=1000,blank=True,verbose_name='备注')
    class Meta:
        db_table = 'shop_items_productsku'
        unique_together = ("outer_id", "product")
        verbose_name=u'库存商品规格'
        verbose_name_plural = u'库存商品规格列表'

    def __unicode__(self):
        return '<%s,%s>'%(self.outer_id,self.properties_alias or self.properties_name)
      
    @property
    def name(self):
        return self.properties_alias or self.properties_name
    
    @property
    def BARCODE(self):
        return self.barcode.strip() or self.product.barcode.strip() or \
                '%s%s'%(self.product.outer_id.strip(),self.outer_id.strip())
    
    @property
    def realnum(self):
        return self.quantity - self.wait_post_num
    
    @property
    def is_out_stock(self):
        if self.quantity<0 or self.wait_post_num <0 :
            self.quantity      = self.quantity >= 0 and self.quantity or 0
            self.wait_post_num = self.wait_post_num >= 0 and self.wait_post_num or 0
            self.save()
        return self.quantity-self.wait_post_num <= 0
    
    @property
    def json(self):
        sku = self
        return {'id':sku.id,
                'outer_id':sku.outer_id,
                'properties_name':sku.properties_name,
                'properties_alias':sku.properties_alias,
                'name':sku.name,
                'cost':sku.cost,
                'std_purchase_price':sku.std_purchase_price,
                'std_sale_price':sku.std_sale_price,
                'agent_price':sku.agent_price,
                'staff_price':sku.staff_price,
                'weight':sku.weight,
                'quantity':sku.quantity,
                'warn_num':sku.warn_num,
                'wait_post_num':sku.wait_post_num,
                'remain_num':sku.remain_num,
                'sync_stock':sku.sync_stock,
                'is_split':sku.is_split,
                'is_match':sku.is_match,
                'post_check':sku.post_check,
                'status':sku.status,
                'is_stock_warn':sku.is_stock_warn,
                'is_assign':sku.is_assign,
                'is_warning':sku.is_warning,
                'status':sku.status,
                'buyer_prompt':sku.buyer_prompt,
                'memo':sku.memo,
                'match_reason':sku.match_reason,
                'districts':sku.get_district_list(),
                'barcode':sku.BARCODE}
        
    def update_quantity(self,num,full_update=False,dec_update=False):
        """
        更新规格库存
        """
        if full_update:
            self.quantity = num
        elif dec_update:
            self.quantity = F('quantity') - num
        else:
            self.quantity = F('quantity') + num
        update_model_fields(self,update_fields=['quantity'])
        
        psku = self.__class__.objects.get(id=self.id)
        self.quantity = psku.quantity
        
        post_save.send(sender=self.__class__,instance=self)
        
        
    def update_wait_post_num(self,num,full_update=False,dec_update=False):
        """
        更新规格待发数:
            full_update:是否全量更新
            dec_update:是否减库存
        """
        if full_update:
            self.wait_post_num = num
        elif dec_update:
            self.wait_post_num = models.F('wait_post_num') - num
        else:
            self.wait_post_num = models.F('wait_post_num') + num
        update_model_fields(self,update_fields=['wait_post_num'])
        
        psku = self.__class__.objects.get(id=self.id)
        self.wait_post_num = psku.wait_post_num 
            
        post_save.send(sender=self.__class__,instance=self)
         
          
    def update_reduce_num(self,num,full_update=False,dec_update=False):
        """
            更新商品库存:
                full_update:是否全量更新
                dec_update:是否减库存
        """
        if full_update:
            self.reduce_num = num
        elif dec_update:
            self.reduce_num = F('reduce_num') - num
        else:
            self.reduce_num = F('reduce_num') + num
        update_model_fields(self,update_fields=['reduce_num'])
        
        self.reduce_num = self.__class__.objects.get(id=self.id).reduce_num
        post_save.send(sender=self.__class__,instance=self)
          
    
    def update_quantity_by_storage_num(self,num):
        
        if num < 0 :
            raise Exception(u'入库更新商品库存数不能小于0')
        
        if num > self.reduce_num:
            real_update_num = num - self.reduce_num
            real_reduct_num = 0
        else:
            real_update_num = 0
            real_reduct_num = self.reduce_num - num
            
        self.update_quantity(real_update_num)
        self.update_reduce_num(real_reduct_num,full_update=True)
    
          
    @property
    def is_stock_warn(self):
        """
        库存是否警告:
        1，如果当前库存小于0；
        2，同步库存（当前库存-预留库存-待发数）小于警告库位 且没有设置警告取消；
        """
        quantity = self.quantity >0 and self.quantity or 0
        remain_num = self.remain_num >0 and self.remain_num or 0
        wait_post_num = self.wait_post_num >0 and self.wait_post_num or 0
        sync_num = quantity - remain_num - wait_post_num
        return sync_num <= 0
    
    @property
    def is_warning(self):
        """
        库存预警:
        1，如果当前能同步的库存小昨日销量；
        """
        quantity      = self.quantity >0 and self.quantity or 0
        remain_num    = self.remain_num >0 and self.remain_num or 0    
        wait_post_num = self.wait_post_num >0 and self.wait_post_num or 0   
        sync_num      = quantity - remain_num - wait_post_num                    
        return self.warn_num >0 and self.warn_num >= sync_num 
    
    def get_district_list(self):
        locations = ProductLocation.objects.filter(product_id=self.product.id,sku_id=self.id)
        return [(l.district.parent_no,l.district.district_no) for l in locations]
    
    def get_districts_code(self):
        """ 商品库中区位,ret_type :c,返回组合后的字符串；o,返回[父编号]-[子编号],... """
        
        locations = self.get_district_list()
        sdict = {}
        for d in locations:
            
            dno = d[1]
            pno = d[0]
            if sdict.has_key(pno):
                sdict[pno].add(dno)
            else:
                sdict[pno] = set([dno])
        
        ds = []
        for k,v in sdict.iteritems():
            ds.append('%s-[%s]'%(k,','.join(v)))
        
        return ','.join(ds)
    
def calculate_product_stock_num(sender, instance, *args, **kwargs):
    """修改SKU库存后，更新库存商品的总库存 """
    product = instance.product
    if not product:
        return
    
    product_skus = product.pskus
    
    if product_skus.count()>0:
        product_dict  = product_skus.aggregate(total_collect_num=Sum('quantity'),
                                               total_warn_num=Sum('warn_num'),
                                               total_remain_num=Sum('remain_num'),
                                               total_post_num=Sum('wait_post_num'),
                                               total_reduce_num=Sum('reduce_num'),
                                               avg_cost=Avg('cost'),
                                               avg_purchase_price=Avg('std_purchase_price'),
                                               avg_agent_price=Avg('agent_price'),
                                               avg_staff_price=Avg('staff_price'))
    
        product.collect_num  =  product_dict.get('total_collect_num') or 0
        product.warn_num     =  product_dict.get('total_warn_num') or 0
        product.remain_num   =  product_dict.get('total_remain_num') or 0
        product.wait_post_num  =  product_dict.get('total_post_num') or 0
        product.reduce_num   =  product_dict.get('reduce_num') or 0
            
        product.cost               = "{0:.2f}".format(product_dict.get('avg_cost') or 0)
        product.std_purchase_price = "{0:.2f}".format(product_dict.get('avg_purchase_price') or 0)
        product.agent_price        = "{0:.2f}".format(product_dict.get('avg_agent_price') or 0)
        product.staff_price        = "{0:.2f}".format(product_dict.get('avg_staff_price') or 0)
        
    product.is_split    = product_skus.filter(is_split=True).count() > 0    
    product.is_match    = product_skus.filter(is_match=True).count() > 0 
    
    product.save()
        
    
post_save.connect(calculate_product_stock_num, sender=ProductSku, dispatch_uid='calculate_product_num')


class Item(models.Model):
    """ 淘宝线上商品 """
    
    num_iid  = models.CharField(primary_key=True,max_length=64,verbose_name='商品ID')

    user     = models.ForeignKey(User,null=True,related_name='items',verbose_name='店铺')
    category = models.ForeignKey(Category,null=True,related_name='items',verbose_name='淘宝分类')
    product  = models.ForeignKey(Product,null=True,related_name='items',verbose_name='关联库存商品')

    outer_id = models.CharField(max_length=64,blank=True,verbose_name='外部编码')
    num      = models.IntegerField(null=True,verbose_name='数量')
    sync_stock = models.BooleanField(default=True,verbose_name='库存同步')
    
    seller_cids = models.CharField(max_length=126,blank=True,verbose_name='卖家分类')
    approve_status = models.CharField(max_length=20,choices=APPROVE_STATUS,blank=True,verbose_name='在售状态')  # onsale,instock
    type       = models.CharField(max_length=12,blank=True,verbose_name='商品类型')
    valid_thru = models.IntegerField(null=True,verbose_name='有效期')
    
    with_hold_quantity = models.IntegerField(default=0,verbose_name='拍下未付款数')
    delivery_time  = models.DateTimeField(null=True,blank=True,verbose_name='发货时间')
    
    price      = models.CharField(max_length=12,blank=True,verbose_name='价格')
    postage_id = models.BigIntegerField(null=True,verbose_name='运费模板ID')

    has_showcase = models.BooleanField(default=False,verbose_name='橱窗推荐')
    modified     = models.DateTimeField(null=True,blank=True,verbose_name='修改时间')

    list_time   = models.DateTimeField(null=True,blank=True,verbose_name='上架时间')
    delist_time = models.DateTimeField(null=True,blank=True,verbose_name='下架时间')

    has_discount = models.BooleanField(default=False,verbose_name='有折扣')

    props = models.TextField(blank=True,verbose_name='商品属性')
    title = models.CharField(max_length=148,blank=True,verbose_name='商品标题')
    property_alias = models.TextField(blank=True,verbose_name='自定义属性')

    has_invoice = models.BooleanField(default=False,verbose_name='有发票')
    pic_url     = models.URLField(verify_exists=False,blank=True,verbose_name='商品图片')
    detail_url  = models.URLField(verify_exists=False,blank=True,verbose_name='详情链接')

    last_num_updated = models.DateTimeField(null=True,blank=True,verbose_name='最后库存同步日期')  #该件商品最后库存同步日期
    
    desc = models.TextField(blank=True,verbose_name='商品描述')
    skus = models.TextField(blank=True,verbose_name='规格')
    
    status = models.BooleanField(default=True,verbose_name='使用')
    class Meta:
        db_table = 'shop_items_item'
        verbose_name = u'线上商品'
        verbose_name_plural = u'线上商品列表'


    def __unicode__(self):
        return '<%s,%s,%s>'%(self.num_iid,self.outer_id,self.title)
    
    @property
    def sku_list(self):
        try:
            return json.loads(self.skus)
        except:
            return {}
    
    @property
    def property_alias_dict(self):
    	property_list = self.property_alias.split(';')
    	property_dict = {}
    	for p in property_list:
            if p:
                r = p.split(':')
                property_dict['%s:%s'%(r[0],r[1])]=r[2]
    	return property_dict
    
    @classmethod
    def get_or_create(cls,user_id,num_iid,force_update=False):
        item,state = Item.objects.get_or_create(num_iid=num_iid)
        if state or force_update:
            try:
                response  = apis.taobao_item_get(num_iid=num_iid,tb_user_id=user_id)
                item_dict = response['item_get_response']['item']
                item      = Item.save_item_through_dict(user_id,item_dict)
                
            except Exception,exc:
                logger.error('商品更新出错(num_iid:%s)'%str(num_iid),exc_info=True)
        return item


    @classmethod
    def save_item_through_dict(cls,user_id,item_dict):
        
        category = Category.get_or_create(user_id,item_dict['cid'])
        if item_dict.has_key('outer_id') and item_dict['outer_id']:
            product,state = Product.objects.get_or_create(outer_id=item_dict['outer_id'])
            if state or not product.name:
                product.collect_num  = item_dict['num']
                product.std_sale_price  = item_dict['price']
                product.agent_price  = item_dict['price']
                product.staff_price  = item_dict['price']
                product.name        = item_dict['title']
            product.pic_path    = item_dict['pic_url']    
            product.save()
    	else:
            #logger.warn('item has no outer_id(num_iid:%s)'%str(item_dict['num_iid']))
            product = None
        
        item,state    = cls.objects.get_or_create(num_iid = item_dict['num_iid'])
        skus = item_dict.get('skus',None)
        item_dict['skus'] = skus and skus or item.skus
        for k,v in item_dict.iteritems():
            hasattr(item,k) and setattr(item,k,v)
            
        if not item.last_num_updated:
            item.last_num_updated = datetime.datetime.now()  
        
        item.user     = User.objects.get(visitor_id=user_id)
        item.product  = product
        item.category = category
        item.status   = True
        item.save()
        return item

class SkuProperty(models.Model):
    """ 
        规格属性
    """
    
    num_iid          = models.BigIntegerField(verbose_name='商品ID')
    sku_id           = models.BigIntegerField(verbose_name='规格ID')
    outer_id         = models.CharField(max_length=32,null=True,blank=True,verbose_name='编码')
    
    properties_name  = models.CharField(max_length=512,null=True,blank=True,verbose_name='规格名称')
    properties       = models.CharField(max_length=512,null=True,blank=True,verbose_name='规格')
    created          = models.DateTimeField(null=True,blank=True,verbose_name='创建日期')
    
    with_hold_quantity = models.IntegerField(default=0,verbose_name='拍下未付款数')
    sku_delivery_time  = models.DateTimeField(null=True,blank=True,verbose_name='发货时间')
    
    modified         = models.DateTimeField(null=True,blank=True,verbose_name='修改日期')
    price            = models.FloatField(default=0.0,verbose_name='价格')
    
    quantity         = models.IntegerField(default=0,verbose_name='数量')    
    status           = models.CharField(max_length=10,blank=True,choices=PRODUCT_STATUS,verbose_name='状态')
    
    class Meta:
        db_table = 'shop_items_skuproperty'
        unique_together = ("num_iid", "sku_id")
        verbose_name = u'线上商品规格'
        verbose_name_plural = u'线上商品规格列表'
        
    @property
    def properties_alias(self):
        return ''.join([p.split(':')[3] for p in self.properties_name.split(';') if p])
    
    @classmethod    
    def save_or_update(cls,sku_dict):
        
        sku,state = cls.objects.get_or_create(num_iid=sku_dict.pop('num_iid'),
                                              sku_id=sku_dict.pop('sku_id'))
        
        for k,v in sku_dict.iteritems():
            if k == 'outer_id' and not v :continue
            hasattr(sku,k) and setattr(sku,k,v)
            
        sku.save()
        
        return sku
    
        

class ProductLocation(models.Model):
    """ 库存商品库位信息 """
    
    product_id   = models.IntegerField(db_index=True,verbose_name='商品ID')
    sku_id       = models.IntegerField(db_index=True,blank=True,null=True,verbose_name='规格ID')
    
    outer_id     = models.CharField(max_length=32,null=False,blank=True,verbose_name='商品编码')
    name         = models.CharField(max_length=64,null=False,blank=True,verbose_name='商品名称')
    
    outer_sku_id     = models.CharField(max_length=32,null=False,blank=True,verbose_name='规格编码')
    properties_name  = models.CharField(max_length=64,null=False,blank=True,verbose_name='规格属性')
    
    district     = models.ForeignKey(DepositeDistrict,
                                     related_name='product_locations',
                                     verbose_name='关联库位')
    
    class Meta:
        db_table = 'shop_items_productlocation'
        unique_together = ("product_id", "sku_id", "district")
        verbose_name = u'商品库位'
        verbose_name_plural = u'商品库位列表'


class ItemNumTaskLog(models.Model):

    id = BigIntegerAutoField(primary_key=True)
    
    user_id  = models.CharField(max_length=64,blank=True,verbose_name='店铺ID')
    outer_id = models.CharField(max_length=64,blank=True,verbose_name='商品编码')
    sku_outer_id = models.CharField(max_length=64,blank=True,verbose_name='规格编码')

    num = models.IntegerField(verbose_name='同步数量')

    start_at   = models.DateTimeField(null=True,blank=True,verbose_name='同步期始')
    end_at     = models.DateTimeField(null=True,blank=True,verbose_name='同步期末')
    
    class Meta:
        db_table = 'shop_items_itemnumtasklog'
        verbose_name=u'库存同步日志'
        verbose_name_plural = u'库存同步日志'

    def __unicode__(self):
        return '<%s,%s,%d>'%(self.outer_id,
                             self.sku_outer_id,
                             self.num)
    
    
class ProductDaySale(models.Model):

    id       = BigIntegerAutoField(primary_key=True)
    
    day_date = models.DateField(verbose_name=u'销售日期')
    
    user_id  = models.BigIntegerField(null=False,verbose_name=u'店铺用户ID')
    product_id  = models.IntegerField(null=False,verbose_name='商品ID')
    sku_id      = models.IntegerField(null=True,verbose_name='规格ID')

    sale_num     = models.IntegerField(default=0.0,verbose_name='销售数量')
    sale_payment = models.FloatField(default=0.0,verbose_name='销售金额')
    sale_refund  = models.FloatField(default=0.0,verbose_name='退款金额')
    
    class Meta:
        db_table = 'shop_items_daysale'
        unique_together = ("day_date","user_id","product_id","sku_id")
        verbose_name    = u'商品销量统计'
        verbose_name_plural = u'商品销量统计'

    def __unicode__(self):
        return '<%s,%d,%d,%s,%d>'%(self.day_date,
                                   self.user_id,
                                   self.product_id,
                                   str(self.sku_id),
                                   self.sale_num)
    
    
