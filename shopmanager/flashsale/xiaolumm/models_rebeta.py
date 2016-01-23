#-*- encoding:utf-8 -*-
from django.db import models
from shopback.base.models import JSONCharMyField

class AgencyOrderRebetaScheme(models.Model):
    """ 代理订单返利模板：代理等级返利设置始终生效，如果商品价格返利选上，则先查找价格返利，然后才查询代理等级返利 """ 
    NORMAL = 1
    CANCEL = 0
    STATUS_CHOICES = (
        (CANCEL,u'关闭'),
        (NORMAL,u'使用')
    )
    name = models.CharField(max_length=64, blank=True, verbose_name=u'计划名称')
    
    agency_rebetas = JSONCharMyField(max_length=10240, blank=True, 
                                default='[{"1":[0,0]}]', 
                                verbose_name=u'代理等级返利设置')
    price_rebetas = JSONCharMyField(max_length=10240, blank=True, 
                                default='[{"100":{"1":[0,0]}}]', 
                                verbose_name=u'商品价格返利设置')
    price_active = models.BooleanField(default=False,verbose_name=u'价格返利生效')
    
    created    = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    modified   = models.DateTimeField(auto_now=True, db_index=True, verbose_name=u'修改时间')
    
    is_default = models.BooleanField(default=False,verbose_name=u'默认设置')
    status     = models.IntegerField(choices=STATUS_CHOICES,default=NORMAL,verbose_name=u'状态')
    
    class Meta:
        db_table = 'xiaolumm_productrebeta'
        verbose_name    = u'妈妈订单返利计划'
        verbose_name_plural = u'妈妈订单返利计划'

    def __unicode__(self):
        return u'<%d,%s>'%(self.id,self.name)
    

        
        
        