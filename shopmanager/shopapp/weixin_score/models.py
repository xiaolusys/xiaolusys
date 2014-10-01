#-*- coding:utf-8 -*-
import datetime
from django.db import models

class SampleFrozenScore(models.Model):
    
    FROZEN   = 0
    CANCLE   = 1
    COMPLETE = 2
    
    STATUS_CHOICES = ((FROZEN,u'冻结'),
                      (CANCLE,u'取消'),
                      (COMPLETE,u'完成'))
    
    user_openid  = models.CharField(max_length=64,db_index=True,verbose_name=u'微信用户ID')
    sample_id    = models.IntegerField(unique=True,verbose_name=u'试用订单ID')
    
    frozen_score = models.IntegerField(default=0,verbose_name=u'冻结积分')
    frozen_time  = models.DateTimeField(null=True,blank=True,verbose_name=u'冻结截止')
    
    modified   = models.DateTimeField(auto_now=True,verbose_name=u'修改时间')
    created    = models.DateTimeField(auto_now_add=True,verbose_name=u'创建日期')
    
    status     = models.IntegerField(choices=STATUS_CHOICES,default=FROZEN,verbose_name=u"状态")    
    class Meta:
        db_table = 'shop_weixin_score_frozen'
        verbose_name = u'试用冻结积分'
        verbose_name_plural = u'使用冻结积分列表'