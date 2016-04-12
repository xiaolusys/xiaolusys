#-*- coding:utf-8 -*-
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save

from core.models import CacheModel, BaseModel

class WeixinUnionID(CacheModel):
    
    openid   = models.CharField(max_length=32,verbose_name=u'OPENID')
    app_key  = models.CharField(max_length=24,verbose_name=u'APPKEY')
    unionid  = models.CharField(max_length=32,db_index=True,verbose_name=u'UNIONID')

    class Meta:
        db_table = 'shop_weixin_unionid'
        unique_together = ('openid', 'app_key')
        app_label = 'weixin'
        verbose_name=u'微信用户授权ID'
        verbose_name_plural = u'微信用户授权ID列表'
    
    def __unicode__(self):
        return u'<%s>'%self.openid
    
from core.weixin import signals

def fetch_weixin_userinfo(sender, appid, resp_data, *args, **kwargs):
    
    from .tasks import task_Update_Weixin_Userinfo
    openid = resp_data.get('openid')
    if not openid or not appid:
        return 
    
    #只对WEIXIN_APPID的公众号授权抓取用户信息
    if appid != settings.WEIXIN_APPID:
        return 
    
    if resp_data.has_key('access_token'):
        task_Update_Weixin_Userinfo.delay(openid,
                                      accessToken=resp_data.get('access_token'))
    else:
        task_Update_Weixin_Userinfo.delay(openid,userinfo=resp_data)

    
signals.signal_weixin_snsauth_response.connect(fetch_weixin_userinfo)


class WeixinUserInfo(BaseModel):
    """
    We make sure every weixin user only have one record in this table.
    -- Zifei 2016-04-12
    """
    unionid  = models.CharField(max_length=32,unique=True,verbose_name=u'UNIONID')
    nick  = models.CharField(max_length=32,blank=True,verbose_name=u'昵称') 
    thumbnail   = models.CharField(max_length=256,blank=True,verbose_name=u'头像') 
    
    class Meta:
        db_table = 'shop_weixin_userinfo'
        app_label = 'weixin'
        verbose_name=u'微信用户基本信息'
        verbose_name_plural = u'微信用户基本信息列表'
    
    def __unicode__(self):
        return u'<%s>'%self.nick


def weixin_userinfo_update_customer(sender,instance,created,*args,**kwargs):
    """
    Every time WeixinUserInfo gets updated, we update corresponding customer (if exists).
    -- Zifei 2016-04-12
    """
    
    from .tasks import task_userinfo_update_customer
    task_userinfo_update_customer.delay(instance)

post_save.connect(weixin_userinfo_update_customer, sender=WeixinUserInfo, dispatch_uid="weixin_userinfo_update_customer")

