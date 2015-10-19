#-*- coding:utf-8 -*-
from django.db import models
import datetime

class CustomShare(models.Model):
    
    title   = models.CharField(max_length=64,blank=True,verbose_name=u'分享标题')
    desc    = models.CharField(max_length=1024,blank=True,verbose_name=u'分享描述')
    share_url = models.CharField(max_length=256,blank=True,verbose_name=u'分享链接')
    share_img = models.CharField(max_length=256,blank=True,verbose_name=u'分享图片(小于32K)')
    
    active_at    = models.DateField(default=datetime.date.today,verbose_name=u'生效时间')
    created      = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')
    modified     = models.DateTimeField(auto_now=True,verbose_name=u'修改时间')
    
    status       = models.BooleanField(default=False,verbose_name=u'使用')
    
    class Meta:
        db_table = 'flashsale_customshare'
        verbose_name=u'特卖/定制分享'
        verbose_name_plural = u'特卖/定制分享列表'
     
    def __unicode__(self):
        return '<%s,%s>'%(self.id,self.title)
    
    def share_link(self,params):
        return self.share_url.format(**params)
    
    
