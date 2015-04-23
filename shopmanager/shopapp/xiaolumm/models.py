#-*- coding:utf-8 -*-
from django.db import models

# Create your models here.


class XiaoluMama(models.Model):
    EFFECT = 'effect'
    INVALID = 'invalid'
    STATUS_CHOICES = (
        (EFFECT,u'有效'),
        (INVALID,u'失效'),
    )

    mobile = models.CharField(max_length=11,db_index=True,unique=True,blank=False,verbose_name=u"手机")
    openid = models.CharField(max_length=64,blank=True,db_index=True,verbose_name=u"OpenId")    
    province = models.CharField(max_length=24,blank=True,verbose_name=u"省份")
    city     = models.CharField(max_length=24,blank=True,verbose_name=u"城市")
    address  = models.CharField(max_length=256,blank=True,verbose_name=u"地址")
    referal_from = models.CharField(max_length=11,db_index=True,blank=True,verbose_name=u"推荐人")
    
    weikefu = models.CharField(max_length=11,db_index=True,blank=True,verbose_name=u"微客服")
    manager = models.IntegerField(default=0,verbose_name=u"管理员")
    
    cash = models.IntegerField(default=0,verbose_name=u"现金")
    pending = models.IntegerField(default=0,verbose_name=u"佣金")

    agencylevel = models.IntegerField(default=1,verbose_name=u"类别")

    created = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')
    status  = models.CharField(max_length=16,blank=True,choices=STATUS_CHOICES,default=EFFECT,verbose_name=u'状态')

    class Meta:
        db_table = 'xiaolumm_xiaolumama'
        verbose_name=u'小鹿妈妈'
        verbose_name_plural = u'小鹿妈妈列表'
    

class AgencyLevel(models.Model):
    category = models.CharField(max_length=11,unique=True,blank=False,verbose_name=u"类别")
    deposit = models.IntegerField(default=0,verbose_name=u"押金")
    cash = models.IntegerField(default=0,verbose_name=u"现金")
    basic_rate = models.IntegerField(default=0,verbose_name=u"基本佣金率")
    target = models.IntegerField(default=0,verbose_name=u"达标额度")
    extra_rate = models.IntegerField(default=0,verbose_name=u"奖励佣金率")
    created = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')

    class Meta:
        db_table = 'xiaolumm_agencylevel'
        verbose_name=u'代理类别'
        verbose_name_plural = u'代理类别列表'


class Clicks(models.Model):
    linkid = models.IntegerField(default=0,db_index=True,verbose_name=u"链接ID")    
    openid = models.CharField(max_length=64,blank=True,db_index=True,verbose_name=u"OpenId")    
    created = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')

    class Meta:
        db_table = 'xiaolumm_clicks'
        verbose_name=u'点击记录'
        verbose_name_plural = u'点击记录列表'



class CashOut(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    COMPLETED = 'completed'
    STATUS_CHOICES = (
        (PENDING,u'待审核'),
        (APPROVED,u'审核通过'),
        (COMPLETED,u'完成'),
    )
    
    mobile = models.CharField(max_length=11,db_index=True,unique=True,blank=False,verbose_name=u"手机")
    value = models.IntegerField(default=0,verbose_name=u"金额")
    status = models.CharField(max_length=16,blank=True,choices=STATUS_CHOICES,default=PENDING,verbose_name=u'状态')
    created = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')

    class Meta:
        db_table = 'xiaolumm_cashout'
        verbose_name=u'提现记录'
        verbose_name_plural = u'提现记录列表'


