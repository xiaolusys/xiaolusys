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
    
    
class ModelProduct(models.Model):
    
    NORMAL = 0
    DELETE = 1
    
    STATUS_CHOICES = ((NORMAL,u'正常'),
                      (DELETE,u'作废'))
    
    name       = models.CharField(max_length=64,db_index=True,verbose_name=u'款式名称')
    
    head_imgs  = models.TextField(blank=True,verbose_name=u'题头照(多张请换行)')
    
    content_imgs = models.TextField(blank=True,verbose_name=u'内容照(多张请换行)')
    
    buy_limit    = models.BooleanField(default=False,verbose_name=u'是否限购')
    per_limit    = models.IntegerField(default=5,verbose_name=u'限购数量')
    
    sale_time    = models.DateField(null=True,blank=True,db_index=True,verbose_name=u'上架日期')
    
    created      = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')
    modified     = models.DateTimeField(auto_now=True,verbose_name=u'修改时间')
    
    status       = models.CharField(max_length=16,db_index=True,
                                    choices=STATUS_CHOICES,
                                    default=NORMAL,verbose_name=u'状态')
    
    class Meta:
        db_table = 'flashsale_modelproduct'
        verbose_name=u'特卖商品/款式'
        verbose_name_plural = u'特卖商品/款式列表'
     
    def __unicode__(self):
        return '<%s,%s>'%(self.id,self.name)
    
    
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
    
    