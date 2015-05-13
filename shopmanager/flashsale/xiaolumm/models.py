#-*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import User as DjangoUser
from shopapp.weixin.models import UserGroup
from .managers import XiaoluMamaManager
# Create your models here.

MM_CLICK_DAY_LIMIT = 2

class XiaoluMama(models.Model):
    
    EFFECT = 'effect'
    INVALID = 'invalid'
    STATUS_CHOICES = (
        (EFFECT,u'有效'),
        (INVALID,u'失效'),
    )
    
    CHARGED  = 'charged'
    UNCHARGE = 'uncharge'
    FROZEN = 'frozen'
    CHARGE_STATUS_CHOICES = (
        (UNCHARGE,u'待接管'),
        (CHARGED,u'已接管'),
        (FROZEN,u'已冻结'),
        )

    mobile = models.CharField(max_length=11,db_index=True,blank=False,verbose_name=u"手机")
    openid = models.CharField(max_length=64,blank=True,unique=True,verbose_name=u"UnionID")    
    province = models.CharField(max_length=24,blank=True,verbose_name=u"省份")
    city     = models.CharField(max_length=24,blank=True,verbose_name=u"城市")
    address  = models.CharField(max_length=256,blank=True,verbose_name=u"地址")
    referal_from = models.CharField(max_length=11,db_index=True,blank=True,verbose_name=u"推荐人")
    
    weikefu = models.CharField(max_length=11,db_index=True,blank=True,verbose_name=u"微客服")
    manager = models.IntegerField(default=0,verbose_name=u"管理员")
    
    cash = models.IntegerField(default=0,verbose_name=u"可用现金")
    pending = models.IntegerField(default=0,verbose_name=u"冻结佣金")

    agencylevel = models.IntegerField(default=1,verbose_name=u"类别")
    user_group = models.ForeignKey(UserGroup,null=True,verbose_name=u"类别")
    
    created = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')
    status  = models.CharField(max_length=16,blank=True,choices=STATUS_CHOICES,
                               default=EFFECT,verbose_name=u'状态')
    
    charge_status = models.CharField(max_length=16,blank=True,db_index=True,
                                       choices=CHARGE_STATUS_CHOICES,
                                       default=UNCHARGE,verbose_name=u'接管状态')
    
    objects = XiaoluMamaManager()
    
    
    class Meta:
        db_table = 'xiaolumm_xiaolumama'
        verbose_name=u'小鹿妈妈'
        verbose_name_plural = u'小鹿妈妈列表'
    
    def get_cash_display(self):
        return float(self.cash/100.0)
    
    get_cash_display.allow_tags = True
    get_cash_display.short_description = u"可用现金"
    
    def get_pending_display(self):
        return float(self.pending/100.0)
    
    get_pending_display.allow_tags = True
    get_pending_display.short_description = u"冻结佣金"
    
    @property
    def cash_money(self):
        return self.get_cash_display()
    
    @property
    def pending_money(self):
        return self.get_pending_display()
    
    @property
    def manager_name(self):
        try:
            return DjangoUser.objects.get(id=self.manager).username
        except:
            return '%s'%self.manager
        
class AgencyLevel(models.Model):
    
    category = models.CharField(max_length=11,unique=True,blank=False,verbose_name=u"类别")
    deposit = models.IntegerField(default=0,verbose_name=u"押金(元)")
    cash = models.IntegerField(default=0,verbose_name=u"现金(元)")
    basic_rate = models.IntegerField(default=0,verbose_name=u"基本佣金率（百分比）")
    target = models.IntegerField(default=0,verbose_name=u"达标额度（元）")
    extra_rate = models.IntegerField(default=0,verbose_name=u"奖励佣金率（百分比）")
    created = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')

    class Meta:
        db_table = 'xiaolumm_agencylevel'
        verbose_name=u'代理类别'
        verbose_name_plural = u'代理类别列表'
        
    def get_cash_display(self):
        return float(self.cash/100.0)
    
    get_cash_display.allow_tags = True
    get_cash_display.short_description = u"现金"
    
    @property
    def cash_money(self):
        return self.get_cash_display()
    
    def get_deposit_display(self):
        return float(self.cash/100.0)
    
    get_deposit_display.allow_tags = True
    get_deposit_display.short_description = u"押金"
    
    @property
    def deposit_money(self):
        return self.get_deposit_display()


class Clicks(models.Model):
    
    CLICK_DAY_LIMIT = MM_CLICK_DAY_LIMIT
    
    linkid = models.IntegerField(default=0,db_index=True,verbose_name=u"链接ID")    
    openid = models.CharField(max_length=64,blank=True,db_index=True,verbose_name=u"OpenId")    
    isvalid = models.BooleanField(default=False,verbose_name='是否有效')
    created = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')

    class Meta:
        db_table = 'xiaolumm_clicks'
        verbose_name=u'点击记录'
        verbose_name_plural = u'点击记录列表'



class CashOut(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    COMPLETED = 'completed'

    STATUS_CHOICES = (
        (PENDING,u'待审核'),
        (APPROVED,u'审核通过'),
        (REJECTED,u'已拒绝'),
        (COMPLETED,u'完成'),
    )
    
    xlmm = models.IntegerField(default=0,db_index=True,verbose_name=u"妈妈编号")
    value = models.IntegerField(default=0,verbose_name=u"金额")
    status = models.CharField(max_length=16,blank=True,choices=STATUS_CHOICES,default=PENDING,verbose_name=u'状态')
    created = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')

    class Meta:
        db_table = 'xiaolumm_cashout'
        verbose_name=u'提现记录'
        verbose_name_plural = u'提现记录列表'
        
    def get_value_display(self):
        return float(self.value / 100.0)
    
    get_value_display.allow_tags = True
    get_value_display.short_description = u"可用现金"
    
    @property
    def value_money(self):
        return self.get_value_display()    
    


class CarryLog(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELED = 'canceled'
    CONSUMED = 'consumed'

    STATUS_CHOICES = (
        (PENDING,u'待确认'),
        (CONFIRMED,u'确定'),
        (CANCELED,u'已退款'),
        (CONSUMED,u'已消费'),
    )

    xlmm = models.BigIntegerField(default=0,db_index=True,verbose_name=u"妈妈编号")
    order_num = models.BigIntegerField(default=0,db_index=True,verbose_name=u"订单编号")
    buyer_nick = models.CharField(max_length=32,blank=True,verbose_name=u'买家昵称')
    value = models.IntegerField(default=0,verbose_name=u"金额")
    status = models.CharField(max_length=16,blank=True,choices=STATUS_CHOICES,default=PENDING,verbose_name=u'状态')
    created = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')
    
    class Meta:
        db_table = 'xiaolumm_carrylog'
        verbose_name=u'补贴记录'
        verbose_name_plural = u'补贴记录列表'
    
    def get_value_display(self):
        return float(self.value / 100.0)
    
    get_value_display.allow_tags = True
    get_value_display.short_description = u"可用现金"
    
    @property
    def value_money(self):
        return self.get_value_display()    
    
