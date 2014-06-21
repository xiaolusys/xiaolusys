#-*- coding:utf8 -*-
import datetime
from django.db import models
from shopback.base.fields import BigIntegerAutoField
from shopback.signals import taobao_logged_in

DEFAULT_GROUP_NAME ='default'

class ValidUserManager(models.Manager):
    def get_query_set(self):
        return super(ValidUserManager, self).get_query_set().filter(is_valid=True)


class TmcMessage(models.Model):
    
    id       = BigIntegerAutoField(primary_key=True)
    user_id  = models.BigIntegerField(db_index=True,verbose_name=u'店铺ID')
    
    topic    = models.CharField(max_length=128,blank=True,verbose_name=u'消息主题')
    pub_app_key   = models.CharField(max_length=64,blank=True,verbose_name=u'发布者APPKEY')
    
    pub_time = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'发布时间') 
    created  = models.DateTimeField(auto_now_add=True,verbose_name=u'入库时间')
       
    content  = models.TextField(max_length=2000,blank=True,verbose_name=u'消息内容')
       
    is_exec   = models.BooleanField(default=False,verbose_name=u'执行') 
    class Meta:
        db_table = 'shop_tmcnotify_message'

    def __unicode__(self):
        return '<%d,%s>'%(self.id,self.topic)
    
    
class TmcUser(models.Model):
    
    user_id     = models.BigIntegerField(db_index=True,verbose_name=u'店铺ID')
    
    user_nick    = models.CharField(max_length=64,blank=True,verbose_name=u'用户昵称')
    
    modified = models.DateTimeField(null=True,blank=True,verbose_name=u'修改时间') 
    created  = models.DateTimeField(null=True,blank=True,verbose_name=u'创建时间')
       
    topics   = models.TextField(max_length=2500,blank=True,verbose_name=u'消息主题')
    group_name = models.CharField(max_length=64,blank=True,default=DEFAULT_GROUP_NAME,verbose_name=u'消息群组')
    quantity   = models.IntegerField(default=100,verbose_name=u'消息数量')
    
    is_valid   = models.BooleanField(default=False,verbose_name=u'是否有效') 
    
    is_primary = models.BooleanField(default=False,verbose_name=u'主用户')
    
    valid_users = ValidUserManager()
    
    class Meta:
        db_table = 'shop_tmcnotify_user'

    def __unicode__(self):
        return '<%d,%s>'%(self.user_id,self.user_nick)
    
    @property
    def topic_set(self):
        
        return set([s.strip() for s in self.topics.split(',')])
    

def createTmcUser(sender,user,*args,**kwargs):
    
    profile = user.get_profile()
    tmc_user,state = TmcUser.objects.get_or_create(
                       user_id=profile.visitor_id)
    tmc_user.user_nick = profile.nick
    tmc_user.save()
    
    
taobao_logged_in.connect(createTmcUser)
    