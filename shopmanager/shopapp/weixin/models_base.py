#-*- coding:utf8 -*-
from django.db import models
from core.models import CacheModel

class WeixinUnionID(CacheModel):
    
    openid   = models.CharField(max_length=32,verbose_name=u'OPENID')
    app_key  = models.CharField(max_length=24,verbose_name=u'APPKEY')
    unionid  = models.CharField(max_length=32,db_index=True,verbose_name=u'UNIONID')

    class Meta:
        db_table = 'shop_weixin_unionid'
        unique_together = ('openid', 'app_key') 
        verbose_name=u'微信用户授权ID'
        verbose_name_plural = u'微信用户授权ID列表'
    
    def __unicode__(self):
        return u'<%s>'%self.openid