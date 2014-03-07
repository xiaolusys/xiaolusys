#-*- coding:utf-8 -*-
import datetime
from django.db import models
from shopback.base.fields import BigIntegerAutoField

class WeiXinAccount(models.Model):
    
    token      = models.CharField(max_length=32,verbose_name=u'TOKEN')
    
    app_id     = models.CharField(max_length=64,verbose_name=u'应用ID')
    app_secret = models.CharField(max_length=128,verbose_name=u'应用SECRET')
    
    access_token = models.CharField(max_length=256,blank=True,verbose_name=u'ACCESS TOKEN')
    
    expires_in = models.BigIntegerField(default=0,verbose_name="使用期限(s)")
    expired    = models.DateTimeField(default=datetime.datetime.now(),verbose_name="上次过期时间")
    
    in_voice   = models.BooleanField(default=False,verbose_name=u'开启语音')
    is_active  = models.BooleanField(default=False,verbose_name=u'激活')
    
    
    class Meta:
        db_table = 'shop_weixin_account'
        verbose_name=u'微信帐号'
        verbose_name_plural = u'微信帐号列表'
        
    @classmethod
    def getAccountInstance(cls):
        try:
            return  cls.objects.get()
        except:
            return AnonymousWeixinAccount()
    
    def isNone(self):
        return False
    
    def isExpired(self):
        return datetime.datetime.now() > self.expired + datetime.timedelta(seconds=self.expires_in)
    
    def checkSignature(self,signature,timestamp,nonce):
        
        import hashlib
        
        sign_array = [self.token,
                      timestamp,
                      nonce]
        sign_array.sort()
        
        sha1_value = hashlib.sha1(''.join(sign_array))

        return sha1_value.hexdigest() == signature
    

            
    
class AnonymousWeixinAccount():
    
    def isNone(self):
        return True
    
    def checkSignature(self,signature,timestamp,nonce):
        return False
    
    def isExpired(self):
        return True

    
    
    