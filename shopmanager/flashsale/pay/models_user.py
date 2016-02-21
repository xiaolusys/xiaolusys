#-*- coding:utf-8 -*-
import random
import datetime
from django.db import models
from django.contrib.auth.models import User as DjangoUser
    
from core.fields import BigIntegerAutoField,BigIntegerForeignKey
from .base import PayBaseModel


class Register(PayBaseModel):
    
    MAX_VALID_COUNT   = 3
    MAX_SUBMIT_TIMES  = 6
    
    id    = BigIntegerAutoField(primary_key=True,verbose_name=u'ID')
    cus_uid      = models.BigIntegerField(db_index=True,default=0,null=True,verbose_name=u"客户ID")
    vmobile      = models.CharField(max_length=11,blank=True,verbose_name=u"待验证手机")
    verify_code  = models.CharField(max_length=8,blank=True,verbose_name=u"验证码")
    
    vemail       = models.CharField(max_length=8,blank=True,verbose_name=u"待验证邮箱")
    mail_code     = models.CharField(max_length=128,blank=True,verbose_name=u"邮箱验证码")
    
    verify_count  = models.IntegerField(default=0,verbose_name=u'验证次数')
    submit_count  = models.IntegerField(default=0,verbose_name=u'提交次数')
    
    mobile_pass   = models.BooleanField(default=False,verbose_name=u"手机验证通过")
    mail_pass     = models.BooleanField(default=False,verbose_name=u"邮箱验证通过")
    
    code_time  = models.DateTimeField(blank=True,null=True,verbose_name=u'短信发送时间')
    mail_time  = models.DateTimeField(blank=True,null=True,verbose_name=u'邮件发送时间')

    initialize_pwd = models.BooleanField(default=False, verbose_name=u"初始化密码")
    
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
        dt = datetime.datetime.now()
        if self.code_time and (dt - self.code_time).days > 1:
            self.verify_count = 1
            self.save()
            return True
        
        if self.verify_count >= self.MAX_VALID_COUNT:
            return False
        return True
    
    def is_verifyable(self):
        """ 能否获取验证码 """
        return self.verifyable()
        
    def is_submitable(self):
        """ 能否提交验证 """
        dt = datetime.datetime.now()
        if self.code_time and (dt - self.code_time).days > 1:
            self.submit_count = 1
            self.save()
            return True
        if self.submit_count > self.MAX_SUBMIT_TIMES:
            return False
        return True
    
    def check_code(self,vcode):
        """ 检查验证码是否正确 """
        if self.verify_code and self.verify_code == vcode:
            self.submit_count = 0
            self.save()
            return True
        self.submit_count += 1
        self.save()
        return False
        
    
class Customer(PayBaseModel):
    
    class Meta:
        db_table = 'flashsale_customer'
        verbose_name=u'特卖用户/客户'
        verbose_name_plural = u'特卖用户/客户列表'
    
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
    user  = models.OneToOneField(DjangoUser,verbose_name= u'原始用户')
    nick  = models.CharField(max_length=32,blank=True,verbose_name=u'昵称') 
    thumbnail   = models.CharField(max_length=256,blank=True,verbose_name=u'头像') 
    mobile  = models.CharField(max_length=11,db_index=True,blank=True,verbose_name=u'手机') 
    email   = models.CharField(max_length=32,db_index=True,blank=True,verbose_name=u'邮箱') 
    phone   = models.CharField(max_length=18,blank=True,verbose_name=u'电话') 
    
    openid  = models.CharField(max_length=28,db_index=True,blank=True,verbose_name=u'微信ID') 
    unionid = models.CharField(max_length=28,db_index=True,verbose_name=u'联合ID')
    
    status     = models.IntegerField(choices=USER_STATUS_CHOICES,default=NORMAL,verbose_name= u'状态') 
    
#     first_paytime   = models.DateTimeField(null=True,blank=True,verbose_name=u'首次购买日期')
#     latest_paytime  = models.DateTimeField(null=True,blank=True,verbose_name=u'最近购买日期')
    
    def __unicode__(self):
        return '%s(%s)'%(self.nick,self.id) 
    
    def is_wxauth(self):
        """ 是否微信授权 """
        if (self.unionid.strip() and 
            datetime.datetime.now() > datetime.datetime(2015,10,30)): #关联用户订单未转移过渡期
            return True
        return False
    
    @classmethod
    def getCustomerByUser(cls,user):
        
        customers = cls.objects.filter(user=user.id)
        if customers.count() > 0:
            return customers[0]
        return None
    
    def getXiaolumm(self):
        
        if not self.unionid:
            return None
        from flashsale.xiaolumm.models import XiaoluMama
        try:
            return XiaoluMama.objects.get(openid=self.unionid, charge_status=XiaoluMama.CHARGED)
        except XiaoluMama.DoesNotExist:
            return None
        
    
    
        
    