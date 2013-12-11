#-*- coding:utf8 -*-
from django.db import models
from shopback.signals import change_addr_signal
from shopback.trades.models import MergeTrade
import logging

logger = logging.getLogger('yunda.handler')

class BranchZone(models.Model):
    
    code     = models.CharField(max_length=10,db_index=True,blank=True,verbose_name='网点编号') 
    name     = models.CharField(max_length=64,blank=True,verbose_name='网点名称') 
    barcode  = models.CharField(max_length=32,blank=True,verbose_name='网点条码')
    
    class Meta:
        db_table = 'shop_yunda_branch'
        verbose_name=u'分拨网点'
        verbose_name_plural = u'分拨网点'
   
    def __unicode__(self):
        return '<%s,%s,%s>'%(self.code,self.barcode,self.name)
    

class ClassifyZone(models.Model):
    
    state    = models.CharField(max_length=32,db_index=True,blank=True,verbose_name='省')
    city     = models.CharField(max_length=32,db_index=True,blank=True,verbose_name='市')
    district = models.CharField(max_length=32,db_index=True,blank=True,verbose_name='区')
    
    branch   = models.ForeignKey(BranchZone,null=True,blank=True,related_name='classify_zones',verbose_name='所属网点')
    zone     = models.CharField(max_length=64,blank=True,verbose_name='集包网点') 
    
    class Meta:
        db_table = 'shop_yunda_zone'
        verbose_name=u'分拨地址'
        verbose_name_plural = u'分拨地址'
   
    def __unicode__(self):
        return '<%s,%s>'%(' '.join([self.state,self.city,self.district]),self.branch or '')
    
    
def change_order_yunda_addr(sender, tid, *args, **kwargs):
   
    from shopapp.yunda.qrcode import modify_order
    mtrade = MergeTrade.objects.get(tid=tid)
    #如果订单非二维码订单，则退出
    if not mtrade.is_qrcode:
        return 
        
    try:
        modify_order([tid])
    except Exception,exc:
        logger.error(exc.message,exc_info=True)
        
change_addr_signal.connect(change_order_yunda_addr,sender=MergeTrade,dispatch_uid='change_order_addr_uniqueid')        
        
