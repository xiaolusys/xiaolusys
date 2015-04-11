#-*- coding:utf-8 -*-
from django.db import models
from shopback.base.fields import BigIntegerAutoField
import logging

class District(models.Model):
    
    FIRST_STAGE  = 1
    SECOND_STAGE = 2
    THIRD_STAGE  = 3
    FOURTH_STAGE = 4
    
    STAGE_CHOICES = ((FIRST_STAGE,u'1'),
                     (SECOND_STAGE,u'2'),
                     (THIRD_STAGE,u'3'),
                     (FOURTH_STAGE,u'4'),)
    
    id     = models.AutoField(primary_key=True,verbose_name=u'ID')
    parent_id = models.IntegerField(null=False,default=0,db_index=True,verbose_name=u'父ID')
    name    = models.CharField(max_length=32,blank=True,verbose_name=u'地址名')
    
    grade   = models.IntegerField(default=0,choices=STAGE_CHOICES,verbose_name=u'等级')
    sort_order = models.IntegerField(default=0,verbose_name=u'优先级')
    
    class Meta:
        db_table = 'flashsale_district' 
        verbose_name = u'省市/区划'
        verbose_name_plural = u'省市/区划列表'
        
    def __unicode__(self):
        
        return '%s,%s'%(self.id,self.name)
    

class UserAddress(models.Model):
    
    cus_uid          =  models.BigIntegerField(verbose_name=u'客户ID')
    
    receiver_name    =  models.CharField(max_length=25,
                                         blank=True,verbose_name=u'收货人姓名')
    receiver_state   =  models.CharField(max_length=16,blank=True,verbose_name=u'省')
    receiver_city    =  models.CharField(max_length=16,blank=True,verbose_name=u'市')
    receiver_district  =  models.CharField(max_length=16,blank=True,verbose_name=u'区')
    
    receiver_address   =  models.CharField(max_length=128,blank=True,verbose_name=u'详细地址')
    receiver_zip       =  models.CharField(max_length=10,blank=True,verbose_name=u'邮编')
    receiver_mobile    =  models.CharField(max_length=11,db_index=True,blank=True,verbose_name=u'手机')
    receiver_phone     =  models.CharField(max_length=20,blank=True,verbose_name=u'电话')
    
    default         = models.BooleanField(default=False,verbose_name=u'默认地址')
    
    class Meta:
        db_table = 'flashsale_address' 
        verbose_name = u'省市/区划'
        verbose_name_plural = u'省市/区划列表'
        
    def __unicode__(self):
        
        return '%s,%s'%(self.id,self.name)
    
    