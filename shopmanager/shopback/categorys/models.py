#-*- coding:utf8 -*-
from django.db import models
from shopback import paramconfig as pcfg
from auth import apis
import logging

logger = logging.getLogger('categorys.handler')
CAT_STATUS = (
    (pcfg.NORMAL,u'正常'),
    (pcfg.DELETE,u'删除'),
) 

class Category(models.Model):

    cid        = models.IntegerField(primary_key=True)
    parent_cid = models.IntegerField(null=True,db_index=True)

    name       = models.CharField(max_length=32)
    is_parent  = models.BooleanField(default=True)
    status     = models.CharField(max_length=7,choices=CAT_STATUS,default=pcfg.NORMAL)
    sort_order = models.IntegerField(null=True)

    class Meta:
        db_table = 'shop_categorys_category'
        verbose_name = u'淘宝类目'
        verbose_name_plural = u'淘宝类目列表'

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
    
    cid     = models.AutoField(primary_key=True,verbose_name=u'类目ID')
    parent_cid = models.IntegerField(null=False,verbose_name=u'父类目ID')
    name    = models.CharField(max_length=32,blank=True,verbose_name=u'类目名')
    
    is_parent  = models.BooleanField(default=True,verbose_name=u'有子类目')
    status  = models.CharField(max_length=7,choices=CAT_STATUS,default=pcfg.NORMAL,verbose_name=u'状态')
    sort_order = models.IntegerField(default=0,verbose_name=u'优先级')
    
    class Meta:
        db_table = 'shop_categorys_productcategory' 
        verbose_name = u'产品类目'
        verbose_name_plural = u'产品类目列表'
        
    def __unicode__(self):
        
        if not self.parent_cid:
            return self.name
        try:
            p_cat = self.__class__.objects.get(cid=self.parent_cid)
        except:
            p_cat = u'【不存在】'
        return '%s / %s'%(p_cat,self.name)
        
    
    
       
       
       