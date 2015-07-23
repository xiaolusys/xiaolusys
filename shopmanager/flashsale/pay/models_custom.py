#-*- coding:utf-8 -*-
from django.db import models
from shopback.items.models import Product

class Productdetail(models.Model):
    
    product  = models.OneToOneField(Product, primary_key=True,related_name='details',verbose_name=u'库存商品')
    
    head_imgs  = models.TextField(blank=True,verbose_name=u'题头照(多张请换行)')

    content_imgs = models.TextField(blank=True,verbose_name=u'内容照(多张请换行)')
    
    buy_limit    = models.BooleanField(default=False,verbose_name=u'是否限购')
    per_limit    = models.IntegerField(default=5,verbose_name=u'限购数量')

    class Meta:
        db_table = 'flashsale_productdetail'
        verbose_name=u'特卖商品/详情'
        verbose_name_plural = u'特卖商品/详情列表'
    
    def __unicode__(self):
        return '<%s,%s>'%(self.product.outer_id,self.product.name)
    
    
# class ModelProduct(models.Model):
#     
#     
# 
#     class Meta:
#         db_table = 'flashsale_modelproduct'
#         verbose_name=u'特卖商品/款式'
#         verbose_name_plural = u'特卖商品/款式列表'
#     
#     def __unicode__(self):
#         return '<%s,%s>'%(self.product.outer_id,self.product.name)
    
    
class GoodShelf(models.Model):
    
    title = models.CharField(max_length=32,db_index=True,blank=True, verbose_name=u'海报标题')
    
    poster_wem_pic   = models.CharField(max_length=256, blank=True, verbose_name=u'女装海报')
    poster_chd_pic   = models.CharField(max_length=256, blank=True, verbose_name=u'童装海报')
    
    poster_wem_page  = models.CharField(max_length=256, blank=True, verbose_name=u'女装专栏')
    poster_chd_page  = models.CharField(max_length=256, blank=True, verbose_name=u'童装专栏')
    
    is_active    = models.BooleanField(default=True,verbose_name=u'上线')
    active_time  = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'上线日期')
    
    created      = models.DateTimeField(null=True,auto_now_add=True,db_index=True,blank=True,verbose_name=u'生成日期')
    modified     = models.DateTimeField(null=True,auto_now=True,blank=True,verbose_name=u'修改日期')
    
    class Meta:
        db_table = 'flashsale_goodshelf'
        verbose_name=u'特卖商品/海报'
        verbose_name_plural = u'特卖商品/海报列表'
    
    def __unicode__(self):
        return u'<海报：%s>'%(self.id)
    
    