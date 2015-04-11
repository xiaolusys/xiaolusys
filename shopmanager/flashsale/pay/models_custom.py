#-*- coding:utf-8 -*-
from django.db import models
from shopback.items.models import Product

class Productdetail(models.Model):
    
    product  = models.OneToOneField(Product, primary_key=True,verbose_name=u'商品ID')
    
    head_img = models.CharField(max_length=256,blank=True,verbose_name=u'题头照')
    ct_img1  = models.CharField(max_length=256,blank=True,verbose_name=u'内容照1')
    ct_img2  = models.CharField(max_length=256,blank=True,verbose_name=u'内容照2')
    ct_img3  = models.CharField(max_length=256,blank=True,verbose_name=u'内容照3')
    ct_img4  = models.CharField(max_length=256,blank=True,verbose_name=u'内容照4')

    class Meta:
        db_table = 'flashsale_productdetail'
        verbose_name=u'特卖商品/详情'
        verbose_name_plural = u'特卖商品/详情列表'
    
    def __unicode__(self):
        return '%s'%self.product