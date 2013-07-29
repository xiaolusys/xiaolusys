#-*- coding:utf8 -*-
from django.db import models
from shopback.base.fields import BigIntegerAutoField


    

class ItemNumTaskLog(models.Model):

    id = BigIntegerAutoField(primary_key=True)
    
    user_id  = models.CharField(max_length=64,blank=True)
    outer_id = models.CharField(max_length=64,blank=True)
    sku_outer_id = models.CharField(max_length=64,blank=True)

    num = models.IntegerField()

    start_at   = models.DateTimeField(null=True,blank=True)
    end_at     = models.DateTimeField(null=True,blank=True)
    
    class Meta:
        db_table = 'shop_syncnum_itemnumtasklog'
        verbose_name=u'库存同步日志'
        verbose_name_plural = u'库存同步日志'

    def __unicode__(self):
        return '<%s,%s,%d>'%(self.outer_id,self.sku_outer_id,self.num)

