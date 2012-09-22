#-*- coding:utf8 -*-
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
from shopback.base.models import BaseModel,NORMAL,DELETE
from shopback.base.fields import BigIntegerAutoField
from shopback.categorys.models import Category,ProductCategory
from shopback.users.models import User
from auth import apis
import logging

logger  = logging.getLogger('items.handler')

ONSALE_STATUS  = 'onsale'
INSTOCK_STATUS = 'instock'

APPROVE_STATUS  = (
    (ONSALE_STATUS,'出售中'),
    (INSTOCK_STATUS,'库中'),
)


PRODUCT_STATUS = (
    (NORMAL,'使用'),
    (DELETE,'删除'),
)

class Product(models.Model):

    outer_id     = models.CharField(max_length=64,primary_key=True)
    name         = models.CharField(max_length=64,blank=True)
    
    category     = models.ForeignKey(ProductCategory,null=True,related_name='products')

    collect_num  = models.IntegerField(null=True)  #库存数
    warn_num     = models.IntegerField(null=True,default=10)    #警戒库位
    price        = models.CharField(max_length=10,blank=True)
    
    created      = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    modified     = models.DateTimeField(null=True,blank=True,auto_now=True)
    
    sync_stock   = models.BooleanField(default=True)
    
    out_stock    = models.BooleanField(default=False)
    status       = models.CharField(max_length=16,db_index=True,choices=PRODUCT_STATUS,default=NORMAL)
    
    class Meta:
        db_table = 'shop_items_product'

    def __unicode__(self):
        return self.name



class ProductSku(models.Model):

    outer_id = models.CharField(max_length=64,null=True,blank=True)
    product  = models.ForeignKey(Product,null=True,related_name='prod_skus')
    
    quantity = models.IntegerField(null=True)
    warn_num     = models.IntegerField(null=True,default=10)    #警戒库位
    
    properties_name = models.TextField(max_length=3000,blank=True)
    properties      = models.TextField(max_length=2000,blank=True)
    
    out_stock    = models.BooleanField(default=False)
    sync_stock   = models.BooleanField(default=True)
    
    modified = models.DateTimeField(null=True,blank=True,auto_now=True)
    status   = models.CharField(max_length=10,db_index=True,choices=PRODUCT_STATUS,default=NORMAL)  #normal,delete

    class Meta:
        db_table = 'shop_items_productsku'
        unique_together = ("outer_id", "product",)

    def __unicode__(self):
        return self.properties_values
    
    def setQuantity(self,num):
        self.quantity = num
        self.save()
        
        total_nums = self.product.prod_skus.aggregate(total_nums=Sum('quantity')).get('total_nums')
        self.product.collect_num = total_nums or 0
        self.product.save()
    
    @property
    def properties_values(self):
        properties_list = self.properties_name.split(';')
        value_list = []
        for properties in properties_list:
            values = properties.split(':')
            value_list.append( values[3] if len(values)==4 else properties)
        return ' '.join(value_list)


class Item(models.Model):
    
    num_iid = models.CharField(primary_key=True,max_length=64)

    user     = models.ForeignKey(User,null=True,related_name='items')
    category = models.ForeignKey(Category,null=True,related_name='items')
    product  = models.ForeignKey(Product,null=True,related_name='items')

    outer_id = models.CharField(max_length=64,blank=True)
    num      = models.IntegerField(null=True)

    seller_cids = models.CharField(max_length=126,blank=True)
    approve_status = models.CharField(max_length=20,choices=APPROVE_STATUS,blank=True)  # onsale,instock
    type = models.CharField(max_length=12,blank=True)
    valid_thru = models.IntegerField(null=True)

    price      = models.CharField(max_length=12,blank=True)
    postage_id = models.BigIntegerField(null=True)

    has_showcase = models.BooleanField(default=False)
    modified     = models.DateTimeField(null=True,blank=True)

    list_time   = models.DateTimeField(null=True,blank=True)
    delist_time = models.DateTimeField(null=True,blank=True)

    has_discount = models.BooleanField(default=False)

    props = models.TextField(max_length=500,blank=True)
    title = models.CharField(max_length=148,blank=True)

    has_invoice = models.BooleanField(default=False)
    pic_url     = models.URLField(verify_exists=False,blank=True)
    detail_url  = models.URLField(verify_exists=False,blank=True)

    last_num_updated = models.DateTimeField(null=True,blank=True)  #该件商品最后库存同步日期
    
    desc = models.TextField(max_length=25000,blank=True)
    skus = models.TextField(max_length=5000,blank=True)

    status = models.BooleanField(default=True)
    class Meta:
        db_table = 'shop_items_item'


    def __unicode__(self):
        return self.num_iid+'---'+self.outer_id+'---'+self.title
    
    @property
    def sku_list(self):
        try:
            return json.loads(self.skus)
        except:
            return {}
 

    @classmethod
    def get_or_create(cls,user_id,num_iid):
        item,state = Item.objects.get_or_create(num_iid=num_iid)
        if state:
            try:
                response  = apis.taobao_item_get(num_iid=num_iid,tb_user_id=user_id)
                item_dict = response['item_get_response']['item']
                item = Item.save_item_through_dict(user_id,item_dict)
            except Exception,exc:
                logger.error('backend update item (num_iid:%s)error'%str(num_iid),exc_info=True)
        return item


    @classmethod
    def save_item_through_dict(cls,user_id,item_dict):
        
        category = Category.get_or_create(user_id,item_dict['cid'])
        try:
            product,state = Product.objects.get_or_create(outer_id=item_dict['outer_id'])
            if state:
                product.collect_num = item_dict['num']
                product.price       = item_dict['price']
                product.name        = item_dict['title']
                product.save()
        except Exception,exc:
            logger.warn('the current item(num_iid:%s)has not set outer_id'%str(item_dict['num_iid']))
            product = None
        
        item,state    = cls.objects.get_or_create(num_iid = item_dict['num_iid'])
        
        for k,v in item_dict.iteritems():
            hasattr(item,k) and setattr(item,k,v)
        
        if not item.last_num_updated:
            item.last_num_updated = datetime.datetime.now()  
        
        item.user     = User.objects.get(visitor_id=user_id)
        item.product  = product
        item.category = category
        item.save()

        return item




