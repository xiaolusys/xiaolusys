#-*- coding:utf8 -*-
from django.db import models
from auth import apis
import logging

logger = logging.getLogger('categorys.handler')
CAT_STATUS = (
    ('normal','正常'),
    ('delete','删除'),
) 

class Category(models.Model):

    cid        = models.IntegerField(primary_key=True)
    parent_cid = models.IntegerField(null=True,db_index=True)

    name       = models.CharField(max_length=32)
    is_parent  = models.BooleanField(default=True)
    status     = models.CharField(max_length=7,choices=CAT_STATUS,default='normal')
    sort_order = models.IntegerField(null=True)

    class Meta:
        db_table = 'shop_categorys_category'


    def __unicode__(self):
        return self.name


    @classmethod
    def get_or_create(cls,user_id,cat_id):
        category,state = Category.objects.get_or_create(cid=cat_id)
        if state:
            try:
                reponse  = apis.taobao_itemcats_get(cids=cat_id,tb_user_id=user_id)
                cat_dict = reponse['itemcats_get_response']['item_cats']['item_cat'][0]
                for key,value in cat_dict.iteritems():
                    hasattr(category,key) and setattr(category,key,value)
                category.save()
            except Exception,exc:
                logger.error('淘宝后台更新该类目(cat_id:%s)出错'%str(cat_id),exc_info=True)

        return category
    
    
class ProductCategory(models.Model):
    
    cid     = models.IntegerField(primary_key=True)
    name    = models.CharField(max_length=32,blank=True)
    parent_cid = models.CharField(max_length=32,blank=True)
    
    is_parent  = models.BooleanField(default=True)
    status  = models.CharField(max_length=7,choices=CAT_STATUS,default='normal')
    sort_order = models.IntegerField(null=True)
    
    class Meta:
        db_table = 'shop_categorys_productcategory' 
        
    def __unicode__(self):
        return self.name
       
       
       