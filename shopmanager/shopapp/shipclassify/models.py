#-*- coding:utf8 -*-
from django.db import models


class ClassifyZone(models.Model):
    
    state    = models.CharField(max_length=32,blank=True)
    city     = models.CharField(max_length=32,blank=True)
    district = models.CharField(max_length=32,blank=True)
    
    zone     = models.CharField(max_length=64,blank=True) 
    code     = models.CharField(max_length=32,blank=True)
    
    class Meta:
        db_table = 'shop_shipclassify_zone'
        verbose_name=u'分拨中心'
        verbose_name_plural = u'分拨中心'
   

    def __unicode__(self):
        return '<%s,%s>'%(' '.join([self.state,self.city,self.district],'%s-%s'%(self.code,self.zone)),self.buyer_nick)