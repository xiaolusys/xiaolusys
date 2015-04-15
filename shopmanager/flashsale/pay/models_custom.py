#-*- coding:utf-8 -*-
from django.db import models
from shopback.items.models import Product

class Productdetail(models.Model):
    
    product  = models.OneToOneField(Product, primary_key=True,related_name='details',verbose_name=u'库存商品')
    
    head_imgs  = models.TextField(blank=True,verbose_name=u'题头照(多张请换行)')

    content_imgs = models.TextField(blank=True,verbose_name=u'内容照(多张请换行)')

    class Meta:
        db_table = 'flashsale_productdetail'
        verbose_name=u'特卖商品/详情'
        verbose_name_plural = u'特卖商品/详情列表'
    
    def __unicode__(self):
        return '<%s,%s>'%(self.product.outer_id,self.product.name)