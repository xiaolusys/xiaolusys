#-*- coding:utf8 -*-
import datetime
from django.db import models
from shopback.base.fields import BigIntegerAutoField
from shopback.base.models import JSONCharMyField


class WeixinUserPicture(models.Model): 
    
    SHARE   = 'SDPP'
    COMMENT = 'HPPP'
    MATCH   = 'BBPP'
    OTHER   = 'OTHER'
    
    PIC_STATUS=((SHARE,u'晒单截图'),
                (COMMENT,u'好评截图'),
                (MATCH,u'宝宝秀'),
                (OTHER,u'其它'),)
    
    APPLY    = 0
    COMPLETE = 1
    INVALID  = 2
    
    PICTURE_STATUS = ((APPLY,u'申请中'),
                      (COMPLETE,u'已提交'),
                      (INVALID,u'已取消'),)
    
    user_openid = models.CharField(max_length=64,db_index=True,verbose_name=u"用户ID")
    
    mobile   = models.CharField(max_length=12,db_index=True,blank=True,verbose_name=u"手机")
    
    pic_url  = models.URLField(max_length=1024,blank=True,verbose_name=u'图片URL')
    pic_type = models.CharField(max_length=8,choices=PIC_STATUS,default=OTHER,verbose_name=u'图片类型')
    pic_memo = models.CharField(max_length=256,blank=True,verbose_name=u'图片备注')
    
    upload_ended  = models.DateTimeField(blank=True,null=True,verbose_name=u'上传有效时间')
    
    modified = models.DateTimeField(auto_now=True,blank=True,null=True,verbose_name=u'修改时间')
    created  = models.DateTimeField(auto_now_add=True,blank=True,null=True,verbose_name=u'创建日期')
    
    status   = models.IntegerField(choices=PICTURE_STATUS,default=APPLY,verbose_name=u'状态')
    
    class Meta:
        db_table = 'shop_weixin_user_picture'
        verbose_name=u'微信用户图片'
        verbose_name_plural = u'微信用户图片列表'
    
    def __unicode__(self):
        return self.get_pic_type_display()
    
    
    