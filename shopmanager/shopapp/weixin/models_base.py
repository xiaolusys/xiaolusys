#-*- coding:utf8 -*-
from django.db import models

class WeixinUnionID(models.Model):
    
    openid   = models.CharField(max_length=32,verbose_name=u'OPENID')
    app_key  = models.CharField(max_length=24,verbose_name=u'APPKEY')
    unionid  = models.CharField(max_length=32,db_index=True,verbose_name=u'UNIONID')
    
    created    = models.DateTimeField(auto_now_add=True,verbose_name=u'创建日期')
    
    class Meta:
        db_table = 'shop_weixin_unionid'
        unique_together = ('openid', 'app_key') 
        verbose_name=u'微信用户UNIONID'
        verbose_name_plural = u'微信用户UNIONID列表'
    
    def __unicode__(self):
        return u'<%s>'%self.openid