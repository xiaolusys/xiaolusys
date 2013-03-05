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
from django.db.models import Sum
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField
from shopback.categorys.models import Category,ProductCategory
from shopback.archives.models import Deposite,DepositeDistrict
from shopback import paramconfig as pcfg
from django.db.models.signals import post_save
from shopback.users.models import User
from auth import apis
import logging

logger  = logging.getLogger('items.handler')



APPROVE_STATUS  = (
    (pcfg.ONSALE_STATUS,'出售中'),
    (pcfg.INSTOCK_STATUS,'库中'),
)


ONLINE_PRODUCT_STATUS = (
    (pcfg.NORMAL,'使用'),
    (pcfg.REMAIN,'待用'),
    (pcfg.DELETE,'作废'),
)

PRODUCT_STATUS = (
    (pcfg.NORMAL,'使用'),
    (pcfg.DELETE,'作废'),
)

class Product(models.Model):
    """ 库存产品 """
    
    outer_id     = models.CharField(max_length=64,verbose_name='采购编码')
    name         = models.CharField(max_length=128,blank=True,verbose_name='产品名称')
    
    category     = models.ForeignKey(ProductCategory,null=True,blank=True,related_name='products',verbose_name='商品分类')
    
    collect_num  = models.IntegerField(default=0,verbose_name='库存数量')
    warn_num     = models.IntegerField(null=True,default=10,verbose_name='警告库位')    #警戒库位
    remain_num   = models.IntegerField(null=True,default=0,verbose_name='预留库位')     #预留库存
    wait_post_num   = models.IntegerField(null=True,default=0,verbose_name='待发数')    #待发数
    
    deposite     = models.ForeignKey(Deposite,null=True,blank=True,related_name='products',verbose_name='仓库')
    deposite_district  = models.ForeignKey(DepositeDistrict,null=True,blank=True,verbose_name='仓库区位')
    
    cost        = models.FloatField(default=0,verbose_name='成本价')
    std_purchase_price = models.FloatField(default=0,verbose_name='标准进价')
    std_sale_price     = models.FloatField(default=0,verbose_name='标准售价')
    agent_price        = models.FloatField(default=0,verbose_name='代理售价')
    staff_price        = models.FloatField(default=0,verbose_name='员工价')
    
    weight      = models.CharField(max_length=128,blank=True,verbose_name='重量(g)')
    #    length      = models.IntegerField(default=0,verbose_name='长(cm)')
    #    width       = models.IntegerField(default=0,verbose_name='宽(cm)')
    #    height      = models.IntegerField(default=0,verbose_name='高(cm)')
    
    created      = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='创建日期')
    modified     = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='修改日期')
    
    status       = models.CharField(max_length=16,db_index=True,choices=PRODUCT_STATUS,default=pcfg.NORMAL,verbose_name='商品状态')
    
    memo         = models.CharField(max_length=1000,blank=True,verbose_name='备注')
    class Meta:
        db_table = 'shop_purchase_product'
        verbose_name=u'库存商品'
        verbose_name_plural = u'库存商品列表'

    def __unicode__(self):
        return '<%s,%s>'%(self.outer_id,self.name)
    
    @property
    def is_out_stock(self):
       return self.collect_num <= 0 or self.collect_num-self.wait_post_num <= 0


class ProductSku(models.Model):
    """ 采购产品规格 """
    
    product      = models.ForeignKey(Product,related_name='product_skus',verbose_name='关联库存产品')
    outer_id     = models.CharField(max_length=64,verbose_name='采购规格编码')
    properties   = models.CharField(max_length=256,blank=True,verbose_name='采购规格名称')

    quantity     = models.IntegerField(default=0,verbose_name='库存数')
    warn_num     = models.IntegerField(null=True,default=10,verbose_name='警告库位')    #警戒库位
    remain_num   = models.IntegerField(null=True,default=0,verbose_name='预留库位')    #预留库存
    wait_post_num = models.IntegerField(null=True,default=0,verbose_name='待发数')    #待发数
    
    deposite_district  = models.ForeignKey(DepositeDistrict,null=True,blank=True,verbose_name='仓库区位')
    
    weight      = models.CharField(max_length=128,blank=True,verbose_name='重量(g)')
    
    created      = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='创建日期')
    modified     = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='修改日期')
    
    status       = models.CharField(max_length=16,db_index=True,choices=PRODUCT_STATUS,default=pcfg.NORMAL,verbose_name='规格状态')
    
    class Meta:
        db_table = 'shop_purchase_productsku'
        verbose_name=u'库存商品规格'
        verbose_name_plural = u'库存商品规格列表'

    def __unicode__(self):
        return '<%s,%s>'%(self.outer_id,self.properties)
    
    @property
    def is_out_stock(self):
       return self.quantity <= 0 or self.quantity-self.wait_post_num <= 0

def calculate_purchase_product_stock_num(sender, instance, *args, **kwargs):
    """修改SKU库存后，更新库存商品的总库存 """
    product = instance.product
    if product:
        collect_num = product.product_skus.filter(status=pcfg.NORMAL)\
            .aggregate(total_nums=Sum('quantity')).get('total_nums')
        warn_num = product.product_skus.filter(status=pcfg.NORMAL)\
            .aggregate(total_nums=Sum('warn_num')).get('total_nums')
        remain_num = product.product_skus.filter(status=pcfg.NORMAL)\
            .aggregate(total_nums=Sum('remain_num')).get('total_nums')
        wait_post_num = product.product_skus.filter(status=pcfg.NORMAL)\
            .aggregate(total_nums=Sum('wait_post_num')).get('total_nums')    
        product.collect_num = collect_num
        product.warn_num = warn_num
        product.remain_num = remain_num
        product.wait_post_num = wait_post_num
        product.save()
    
post_save.connect(calculate_purchase_product_stock_num, sender=ProductSku, dispatch_uid='calculate_product_num')


class OnlineProduct(models.Model):
    """ 抽象商品（根据淘宝外部编码)，描述：
        1,映射淘宝出售商品与采购商品桥梁；
        2,淘宝线上库存管理的核心类；
    """
    
    outer_id     = models.CharField(max_length=64,unique=True,null=False,blank=True,verbose_name='外部编码')
   
    name         = models.CharField(max_length=64,blank=True,verbose_name='商品名称')
    
    purchase_product = models.ForeignKey(Product,null=True,blank=True,related_name='online_products',verbose_name='关联采购商品')
    category     = models.ForeignKey(ProductCategory,null=True,blank=True,related_name='online_products',verbose_name='内部分类')
    
    pic_path     = models.CharField(max_length=256,blank=True)
    
    collect_num  = models.IntegerField(default=0,verbose_name='库存数(已废弃)')  #库存数
    warn_num     = models.IntegerField(null=True,default=10,verbose_name='警告库位')    #警戒库位
    remain_num   = models.IntegerField(null=True,default=0,verbose_name='预留库位')    #预留库存
    price        = models.CharField(max_length=10,blank=True,verbose_name='参考价格')
    
    created      = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='创建时间')
    modified     = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='修改时间')
    
    sync_stock   = models.BooleanField(default=True,verbose_name='库存同步')
    out_stock    = models.BooleanField(default=False,verbose_name='缺货')
    is_assign    = models.BooleanField(default=False,verbose_name='库位警告') #是否手动分配库存，当库存充足时，系统自动设为False，手动分配过后，确定后置为True
    
    status       = models.CharField(max_length=16,db_index=True,choices=ONLINE_PRODUCT_STATUS,default=pcfg.NORMAL,verbose_name='商品状态')
    
    class Meta:
        db_table = 'shop_items_product'
        verbose_name = u'淘宝商品'
        verbose_name_plural = u'淘宝商品列表'

    def __unicode__(self):
        return self.name
    
    @property
    def pskus(self):
        return self.prod_skus.filter(status=pcfg.NORMAL)


class OnlineProductSku(models.Model):
    """ 抽象商品规格（根据淘宝规格外部编码），描述：
        1,映射淘宝出售商品规格与采购商品规格桥梁；
        2,库存管理的规格核心类；
    """
    outer_id = models.CharField(max_length=64,null=True,blank=True,verbose_name='规格外部编码')
    
    prod_outer_id = models.CharField(max_length=64,db_index=True,blank=True,default='',verbose_name='商品外部编码')
    product  = models.ForeignKey(OnlineProduct,null=True,related_name='prod_skus',verbose_name='商品')
    purchase_product_sku = models.ForeignKey(ProductSku,null=True,blank=True,related_name='prod_skus',verbose_name='关联采购规格')
    
    quantity = models.IntegerField(default=0,verbose_name='库存数(已废弃)')
    warn_num     = models.IntegerField(null=True,default=10,verbose_name='警戒库位')    #警戒库位
    remain_num   = models.IntegerField(null=True,default=0,verbose_name='预留库位')    #预留库存
    
    properties_name = models.TextField(max_length=200,blank=True,verbose_name='规格属性')
    properties      = models.TextField(max_length=200,blank=True,verbose_name='属性编码')
    
    out_stock    = models.BooleanField(default=False,verbose_name='缺货') 
    sync_stock   = models.BooleanField(default=True,verbose_name='库存同步') 
    is_assign    = models.BooleanField(default=False,verbose_name='已分配库存') #是否手动分配库存，当库存充足时，系统自动设为False，手动分配过后，确定后置为True
    
    modified = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='修改时间')
    status   = models.CharField(max_length=10,db_index=True,choices=ONLINE_PRODUCT_STATUS,default=pcfg.NORMAL,verbose_name='规格状态')  #normal,delete
    
    class Meta:
        db_table = 'shop_items_productsku'
        unique_together = ("outer_id", "product",)
        verbose_name=u'淘宝商品规格'
        verbose_name_plural = u'淘宝商品规格列表'

    def __unicode__(self):
        return self.properties_values
      
    @property
    def properties_values(self):
        properties_list = self.properties_name.split(';')
        value_list = []
        for properties in properties_list:
            values = properties.split(':')
            value_list.append( '%s'%values[3] if len(values)==4 else properties)
        return ','.join(value_list)


class Item(models.Model):
    """ 淘宝线上商品 """
    
    num_iid  = models.CharField(primary_key=True,max_length=64,verbose_name='商品ID')

    user     = models.ForeignKey(User,null=True,related_name='items',verbose_name='店铺')
    category = models.ForeignKey(Category,null=True,related_name='items',verbose_name='淘宝分类')
    product  = models.ForeignKey(OnlineProduct,null=True,related_name='items',verbose_name='关联库存商品')

    outer_id = models.CharField(max_length=64,blank=True,verbose_name='外部编码')
    num      = models.IntegerField(null=True,verbose_name='数量')

    seller_cids = models.CharField(max_length=126,blank=True,verbose_name='卖家分类')
    approve_status = models.CharField(max_length=20,choices=APPROVE_STATUS,blank=True,verbose_name='在售状态')  # onsale,instock
    type       = models.CharField(max_length=12,blank=True,verbose_name='商品类型')
    valid_thru = models.IntegerField(null=True,verbose_name='有效期')

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

    status = models.BooleanField(default=True,verbose_name='系统状态')
    class Meta:
        db_table = 'shop_items_item'
        verbose_name = u'线上商品'
        verbose_name_plural = u'线上商品列表'



    def __unicode__(self):
        return self.num_iid+'---'+self.outer_id+'---'+self.title
    
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
                item = Item.save_item_through_dict(user_id,item_dict)
            except Exception,exc:
                logger.error('商品更新出错(num_iid:%s)'%str(num_iid),exc_info=True)
        return item


    @classmethod
    def save_item_through_dict(cls,user_id,item_dict):
        
        category = Category.get_or_create(user_id,item_dict['cid'])
        if item_dict.has_key('outer_id') and item_dict['outer_id']:
            product,state = OnlineProduct.objects.get_or_create(outer_id=item_dict['outer_id'])
            if not product.name:
                product.collect_num = item_dict['num']
                product.price       = item_dict['price']
                product.name        = item_dict['title']
            product.pic_path    = item_dict['pic_url']    
            product.save()
    	else:
            #logger.warn('item has no outer_id(num_iid:%s)'%str(item_dict['num_iid']))
            product = None
        
        item,state    = cls.objects.get_or_create(num_iid = item_dict['num_iid'])
        item_dict['skus'] = item_dict.get('skus','{}')
        for k,v in item_dict.iteritems():
            hasattr(item,k) and setattr(item,k,v)

        if not item.last_num_updated:
            item.last_num_updated = datetime.datetime.now()  
        
        item.user     = User.objects.get(visitor_id=user_id)
        item.product  = product
        item.category = category
        item.save()

        return item




