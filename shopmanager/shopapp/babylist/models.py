#-*- coding:utf8 -*-
__author__ = 'meixqhi'
from django.db import models
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey

class BabyPhone(models.Model):
    
    id         = BigIntegerAutoField(primary_key=True,verbose_name='手机号')
    
    father     = models.CharField(max_length=64,blank=True,db_index=True,verbose_name='亲属名')
    
    state      = models.CharField(max_length=32,blank=True,verbose_name='省')
    
    city       = models.CharField(max_length=32,blank=True,verbose_name='市')
    
    address    = models.CharField(max_length=256,blank=True,verbose_name='地址')
    sex        = models.CharField(max_length=3,blank=True,verbose_name='性别')
    
    born       = models.DateField(null=True,blank=True,verbose_name='出生日期')
    code       = models.CharField(max_length=64,blank=True,verbose_name='邮编')
    
    hospital   = models.CharField(max_length=64,blank=True,verbose_name='医院')
    
    class Meta:
        db_table = 'shop_babylist_babyphone'
        verbose_name = u'新生儿童信息'
        verbose_name_plural = u'新生儿童信息列表'

    def __unicode__(self):
        return '<%d,%s,%s>'%(self.id,self.father,self.hospital)