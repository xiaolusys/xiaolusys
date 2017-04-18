#-*- coding:utf-8 -*-
from __future__ import unicode_literals

import datetime
from django.db import models

class PickGroup(models.Model):
    
    name      = models.CharField(max_length=100,unique=True,blank=True,verbose_name=u'组')
    wave_no   = models.IntegerField(default=0,unique=True,verbose_name=u'批号')    
    
    modified  = models.DateTimeField(auto_now=True,blank=True,null=True,verbose_name=u'修改日期')
    created   = models.DateTimeField(auto_now_add=True,blank=True,null=True,verbose_name=u'创建日期')
    
    class Meta:
        db_table = 'supplychain_pick_group'
        app_label = 'wavepick'
        verbose_name = u'批号/组'
        verbose_name_plural = u'批号/组列表'
        
    def generateWaveNoByGroup(self):
        
        cnt = 0
        while True:
            try:
                self.wave_no = self.wave_no + 10
                self.save()
            except:
                cnt += 1
                if cnt >20:
                    break
            else:
                return self.wave_no
                
        return None
        

# Create your models here.
class WavePick(models.Model):
    
    ACTIVE   = 0
    DEACTIVE = 1
    STATUS_CHOICES = ((ACTIVE,u'未分捡'),
                      (DEACTIVE,u'分捡'),)
    
    wave_no  = models.IntegerField(db_index=True,verbose_name=u'批号')
    out_sid  = models.CharField(max_length=64,verbose_name=u'物流编号')
#    tid     = models.BigIntegerField(null=False,db_index=True,verbose_name=u'交易ID')
#    oid     = models.BigIntegerField(null=False,db_index=True,verbose_name=u'订单ID')
    serial_no  = models.IntegerField(null=False,db_index=True,verbose_name=u'序号')
    group_id = models.IntegerField(null=False,db_index=True,verbose_name=u'组')
    
    created = models.DateTimeField(auto_now_add=True,blank=True,null=True,verbose_name=u'创建日期')
    
    status  = models.IntegerField(choices=STATUS_CHOICES,default=ACTIVE,verbose_name=u"状态")
    
    class Meta:
        db_table = 'supplychain_pick_wave'
        unique_together = ('wave_no','out_sid')
        app_label = 'wavepick'
        verbose_name = u'批号/物流单号'
        verbose_name_plural = u'批号/物流单号'
        
        
        
class PickItem(models.Model):
    
    wave_no = models.IntegerField(null=True,db_index=True,verbose_name=u'批号')
    out_sid = models.CharField(max_length=64,db_index=True,blank=True,verbose_name=u'物流编号')
    serial_no  = models.IntegerField(null=True,db_index=True,verbose_name=u'序号')    
    
    outer_sku_id = models.CharField(max_length=20,blank=True,verbose_name=u'规格外部编码')
    outer_id = models.CharField(max_length=64,blank=True,verbose_name=u'商品外部编码')
    
    barcode  = models.CharField(max_length=64,db_index=True,blank=True,verbose_name=u'识别码')
    title    = models.CharField(max_length=256,blank=True,verbose_name=u'商品名称')
    item_num = models.IntegerField(default=0,db_index=True,verbose_name=u'数量')
    
    identity = models.IntegerField(default=0,db_index=True,verbose_name=u'商品标识')    
    
    class Meta:
        db_table = 'supplychain_pick_item'
        unique_together = ('out_sid','outer_id','outer_sku_id')
        app_label = 'wavepick'
        verbose_name = u'捡货明细'
        verbose_name_plural = u'捡货明细列表'
        
        
class PickPublish(models.Model):
    
    group_id = models.IntegerField(db_index=True,unique=True,verbose_name=u'组号')
    
    pvalue   = models.CharField(max_length=24,blank=False,default="000000"*4,verbose_name=u'显示值')
    
    modified  = models.DateTimeField(auto_now=True,blank=True,null=True,verbose_name=u'修改日期')
    created   = models.DateTimeField(auto_now_add=True,blank=True,null=True,verbose_name=u'创建日期')
    
    class Meta:
        db_table = 'supplychain_pick_publish'
        app_label = 'wavepick'
        verbose_name = u'捡货LED值'
        verbose_name_plural = u'捡货LED值列表'
        
        
