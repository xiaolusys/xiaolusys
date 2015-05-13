#-*- coding:utf-8 -*-
import random
from django.db import models
from django.contrib.auth.models import User as DjangoUser
    
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
    

    
class Register(models.Model):
    
    MAX_VALID_COUNT   = 3
    MAX_SUBMIT_TIMES  = 6
    
    id    = BigIntegerAutoField(primary_key=True,verbose_name=u'ID')
    
    cus_uid      = models.BigIntegerField(db_index=True,null=True,verbose_name=u"客户ID")
    
    vmobile      = models.CharField(max_length=11,blank=True,verbose_name=u"待验证手机")
    verify_code  = models.CharField(max_length=8,blank=True,verbose_name=u"验证码")
    
    vemail       = models.CharField(max_length=8,blank=True,verbose_name=u"待验证手机")
    mail_code     = models.CharField(max_length=128,blank=True,verbose_name=u"邮箱验证码")
    
    verify_count  = models.IntegerField(default=0,verbose_name=u'验证次数')
    submit_count  = models.IntegerField(default=0,verbose_name=u'提交次数')
    
    mobile_pass   = models.BooleanField(default=False,verbose_name=u"手机验证通过")
    mail_pass     = models.BooleanField(default=False,verbose_name=u"邮箱验证通过")
    
    code_time  = models.DateTimeField(blank=True,null=True,verbose_name=u'短信发送时间')
    mail_time  = models.DateTimeField(blank=True,null=True,verbose_name=u'邮件发送时间')
    
    created     = models.DateTimeField(auto_now_add=True,verbose_name=u'创建日期')
    modified   = models.DateTimeField(auto_now=True,verbose_name=u'修改日期')
    
    class Meta:
        db_table = 'flashsale_register'
        verbose_name=u'特卖用户/注册'
        verbose_name_plural = u'特卖用户/注册列表'
        
    def __unicode__(self):
        return '<%s>'%(self.id)
    
    def genValidCode(self):
        return ''.join(random.sample(list('0123456789'),6))
    
    def genMailCode(self):
        return ''.join(random.sample(list('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_'),32))
    
    def verifyable(self):
        
        if self.is_verify:
            return False
        if self.valid_count >= self.MAX_FALD_TIMES:
            return False
        if self.submit_count >= self.MAX_SUBMIT_TIMES:
            return False
        return True
    

    
class Customer(models.Model):
    
    NORMAL = 1     #正常
    INACTIVE = 0   #未激活
    DELETE = 2     #删除
    FREEZE = 3     #冻结
    SUPERVISE = 4  #监管
    
    USER_STATUS_CHOICES = (
        (NORMAL,u'正常'),
        (INACTIVE,u'未激活'),
        (DELETE,u'删除'),
        (FREEZE,u'冻结'),
        (SUPERVISE,u'监管'),
    )
    
    id    = BigIntegerAutoField(primary_key=True,verbose_name=u'客户ID')
    
    user  = BigIntegerForeignKey(DjangoUser,unique=True,verbose_name= u'原始用户')
    
    nick  = models.CharField(max_length=32,blank=True,verbose_name=u'昵称') 
    mobile  = models.CharField(max_length=11,db_index=True,blank=True,verbose_name=u'手机') 
    email   = models.CharField(max_length=32,db_index=True,blank=True,verbose_name=u'邮箱') 
    phone   = models.CharField(max_length=18,blank=True,verbose_name=u'电话') 
    
    openid  = models.CharField(max_length=28,db_index=True,blank=True,verbose_name=u'微信ID') 
    unionid = models.CharField(max_length=28,db_index=True,blank=True,verbose_name=u'联合ID') 
    
    status     = models.IntegerField(choices=USER_STATUS_CHOICES,default=NORMAL,verbose_name= u'状态') 
    
    created     = models.DateTimeField(auto_now_add=True,verbose_name=u'创建日期')
    modified   = models.DateTimeField(auto_now=True,verbose_name=u'修改日期')
    
    class Meta:
        db_table = 'flashsale_customer'
        verbose_name=u'特卖用户/客户'
        verbose_name_plural = u'特卖用户/客户列表'
        
    def __unicode__(self):
        return '%s(%s)'%(self.nick,self.id) 
    
    @classmethod
    def getCustomerByUser(cls,user):
        
        customers = cls.objects.filter(user=user.id)
        if customers.count() > 0:
            return customers[0]
        return None
        
    