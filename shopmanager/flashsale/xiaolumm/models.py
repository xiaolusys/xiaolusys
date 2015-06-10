#-*- coding:utf-8 -*-
import datetime
from django.db import models
from django.contrib.auth.models import User as DjangoUser
from shopapp.weixin.models import UserGroup
from .managers import XiaoluMamaManager
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
# Create your models here.

MM_CLICK_DAY_LIMIT = 1
MM_CLICK_DAY_BASE_COUNT  = 50
MM_CLICK_PER_ORDER_PLUS_COUNT = 30

class XiaoluMama(models.Model):
    
    EFFECT = 'effect'
    INVALID = 'invalid'
    STATUS_CHOICES = (
        (EFFECT,u'有效'),
        (INVALID,u'失效'),
    )
    
    NONE    = 'none'
    PROFILE = 'profile'
    PAY     = 'pay'
    PASS    = 'pass'
    PROGRESS_CHOICES = (
        (NONE,u'未申请'),
        (PROFILE,u'填写资料'),
        (PAY,u'支付押金'),
        (PASS,u'申请成功'),
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
    
    cash    = models.IntegerField(default=0,verbose_name=u"可用现金")
    pending = models.IntegerField(default=0,verbose_name=u"冻结佣金")
    
    agencylevel = models.IntegerField(default=1,verbose_name=u"代理类别")
    user_group  = BigIntegerForeignKey(UserGroup,null=True,verbose_name=u"分组")
    
    created = models.DateTimeField(auto_now_add=True,db_index=True,verbose_name=u'创建时间')
    status  = models.CharField(max_length=16,blank=True,choices=STATUS_CHOICES,
                               default=EFFECT,verbose_name=u'状态')
    
    charge_status = models.CharField(max_length=16,blank=True,db_index=True,
                                       choices=CHARGE_STATUS_CHOICES,
                                       default=UNCHARGE,verbose_name=u'接管状态')
    
    progress = models.CharField(max_length=8,blank=True,db_index=True,
                               choices=PROGRESS_CHOICES,
                               default=NONE,verbose_name=u'申请进度')
    
    objects = XiaoluMamaManager()
    
    class Meta:
        db_table = 'xiaolumm_xiaolumama'
        verbose_name=u'小鹿妈妈'
        verbose_name_plural = u'小鹿妈妈列表'
        
    def __unicode__(self):
        return '%s'%self.id
    
    def get_cash_display(self):
        return self.cash / 100.0
    
    get_cash_display.allow_tags = True
    get_cash_display.admin_order_field = 'cash'
    get_cash_display.short_description = u"可用现金"
    
    def get_pending_display(self):
        return self.pending / 100.0
    
    get_pending_display.allow_tags = True
    get_cash_display.admin_order_field = 'pending'
    get_pending_display.short_description = u"冻结佣金"
    
    @property
    def cash_money(self):
        return self.get_cash_display()
    
    @property
    def pending_money(self):
        return self.get_pending_display()
    
    @property
    def manager_name(self):
        """ 获取小鹿妈妈管理员 """
        try:
            return DjangoUser.objects.get(id=self.manager).username
        except:
            return '%s'%self.manager

    def exam_Passed(self):
        
        from flashsale.mmexam.models import Result
        results = Result.objects.filter(daili_user=self.openid)
        if results.count() > 0  and results[0].is_Exam_Funished():
            return True
        return False
    
    def get_Mama_Agency_Rebeta_Rate(self):
        """ 获取代理妈妈获取子级代理的提成点数 """
        if self.agencylevel == 2:
            return 0.05
        return 0
        
    def get_Mama_Order_Rebeta_Rate(self):
        """ 获取小鹿妈妈订单提成点数 """
        agency_levels = AgencyLevel.objects.filter(id=self.agencylevel)
        if agency_levels.count() == 0:
            return 0
        agency_level = agency_levels[0]
        return agency_level.get_Rebeta_Rate()
    
    def get_Mama_Click_Price(self,ordernum):
        """ 获取小鹿妈妈点击价格 """
        agency_levels = AgencyLevel.objects.filter(id=self.agencylevel)
        if agency_levels.count() == 0:
            return 0
        agency_level = agency_levels[0]
        return agency_level.get_Click_Price(ordernum)
        
    def get_Mama_Max_Valid_Clickcount(self,ordernum):
        """ 获取小鹿妈妈最大有效点击数 """
        agency_levels = AgencyLevel.objects.filter(id=self.agencylevel)
        if agency_levels.count() == 0:
            return 0
        agency_level = agency_levels[0]
        return agency_level.get_Max_Valid_Clickcount(ordernum)
    
# from .clickprice import CLICK_TIME_PRICE

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
        
    def __unicode__(self):
        return '%s'%self.id
        
    def get_basic_rate_display(self):
        return self.basic_rate / 100.0
    
    get_basic_rate_display.allow_tags = True
    get_basic_rate_display.short_description = u"基本佣金率"
    
    @property
    def basic_rate_percent(self):
        return self.get_basic_rate_display()
    
    def get_extra_rate_display(self):
        return self.extra_rate / 100.0
    
    get_extra_rate_display.allow_tags = True
    get_extra_rate_display.admin_order_field = 'extra_rate'
    get_extra_rate_display.short_description = u"奖励佣金率"
    
    @property
    def extra_rate_percent(self):
        return self.get_extra_rate_display()
    
    def get_Click_Price(self,order_num):
        
        if self.id < 2:
            return 0
        
        click_price = 0.2
        if order_num > 2:
            click_price = 0.5
        else:
            click_price += order_num * 0.1
        
        return click_price * 100
    
    def get_Max_Valid_Clickcount(self,order_num):
        
        return MM_CLICK_DAY_BASE_COUNT + MM_CLICK_PER_ORDER_PLUS_COUNT * order_num
        
    
    def get_Click_Price_List(self,target_date):
        
        d = target_date
        t_from = datetime.datetime(d.year,d.month,d.day,0,0,0)
        t_to   = datetime.datetime(d.year,d.month,d.day,23,59,59)
        
        price_list = []
        for ctp in CLICK_TIME_PRICE:
            if ctp[0] > t_to or ctp[1] < t_from:
                continue
            
            if ctp[0] > t_from:
                price_list.append((t_from,ctp[0],0))
            
            if ctp[1] > t_to:
                price_list.append((ctp[0],t_to,0))
            
            if ctp[1] < t_to:
                price_list.append((t_to,ctp[1],0))
            
        
    
    def get_Rebeta_Rate(self,*args,**kwargs):
        return self.basic_rate / 100.0
    

# class ClickPrice(models.Model):
#     
#     order_num  = models.IntegerField(default=0,verbose_name=u'订单数量')
#     start_time = models.DateTimeField(verbose_name=u'开始时间')
#     end_time   = models.DateTimeField(verbose_name=u'结束时间')
#     click_price = models.IntegerField(default=0,verbose_name=u'点击价格')
# 
#     class Meta:
#         db_table = 'xiaolumm_click_price'
#         verbose_name=u'点击价格'
#         verbose_name_plural = u'点击价格列表'
# 
#     def __unicode__(self):
#         return '%s'%self.id


class Clicks(models.Model):
    
    CLICK_DAY_LIMIT = MM_CLICK_DAY_LIMIT
    
    linkid = models.IntegerField(default=0,db_index=True,verbose_name=u"链接ID")    
    openid = models.CharField(max_length=64,blank=True,db_index=True,verbose_name=u"OpenId")    
    isvalid = models.BooleanField(default=False,verbose_name='是否有效')
    click_time = models.DateTimeField(db_index=True,verbose_name=u'点击时间')
    created = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')

    class Meta:
        db_table = 'xiaolumm_clicks'
        verbose_name=u'点击记录'
        verbose_name_plural = u'点击记录列表'

    def __unicode__(self):
        return '%s'%self.id
    

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
    value = models.IntegerField(default=0,verbose_name=u"金额(分)")
    status = models.CharField(max_length=16,blank=True,choices=STATUS_CHOICES,default=PENDING,verbose_name=u'状态')
    
    approve_time = models.DateTimeField(blank=True,null=True,verbose_name=u'审核时间')
    created = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')

    class Meta:
        db_table = 'xiaolumm_cashout'
        verbose_name=u'提现记录'
        verbose_name_plural = u'提现记录列表'
        
    def __unicode__(self):
        return '%s'%self.id
        
    def get_value_display(self):
        return self.value / 100.0
    
    get_value_display.allow_tags = True
    get_value_display.admin_order_field = 'value'
    get_value_display.short_description = u"可用现金"
    
    @property
    def value_money(self):
        return self.get_value_display()    
    


class CarryLog(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELED = 'canceled'

    STATUS_CHOICES = (
        (PENDING,u'待确认'),
        (CONFIRMED,u'确定'),
        (CANCELED,u'已取消'),
    )
    
    ORDER_REBETA  = 'rebeta'
    ORDER_BUY     = 'buy'
    CLICK_REBETA  = 'click'
    REFUND_RETURN = 'refund'
    CASH_OUT      = 'cashout'
    DEPOSIT       = 'deposit'
    THOUSAND_REBETA = 'thousand'
    AGENCY_SUBSIDY  = 'subsidy'
    MAMA_CONTRIBU   = 'contrib'
    
    LOG_TYPE_CHOICES = (
        (ORDER_REBETA,u'订单返利'),
        (ORDER_BUY,u'消费支出'),
        (REFUND_RETURN,u'退款返现'),
        (CLICK_REBETA,u'点击兑现'),
        (CASH_OUT,u'钱包提现'),
        (DEPOSIT,u'押金'),
        (THOUSAND_REBETA,u'千元提成'),
        (AGENCY_SUBSIDY,u'代理补贴'),
        (MAMA_CONTRIBU,u'妈妈贡献')
    )
    
    CARRY_OUT = 'out'
    CARRY_IN  = 'in'
    CARRY_TYPE_CHOICES = (
        (CARRY_OUT,u'支出'),
        (CARRY_IN,u'收入'),
    )
    
    xlmm       = models.BigIntegerField(default=0,db_index=True,verbose_name=u"妈妈编号")
    order_num  = models.BigIntegerField(default=0,db_index=True,verbose_name=u"订单编号")
    buyer_nick = models.CharField(max_length=32,blank=True,verbose_name=u'买家昵称')
    value      = models.IntegerField(default=0,verbose_name=u"金额")
    
    log_type   = models.CharField(max_length=8,blank=True,
                                  choices=LOG_TYPE_CHOICES,
                                  default=ORDER_REBETA,verbose_name=u"类型")
    
    carry_type = models.CharField(max_length=8,blank=True,
                                  choices=CARRY_TYPE_CHOICES,
                                  default=CARRY_OUT,verbose_name=u"盈负")
    
    status     = models.CharField(max_length=16,blank=True,
                                  choices=STATUS_CHOICES,
                                  default=CONFIRMED,verbose_name=u'状态')
    
    carry_date = models.DateField(default=datetime.date.today,verbose_name=u'业务日期')
    created    = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')
    
    class Meta:
        db_table = 'xiaolumm_carrylog'
        verbose_name=u'妈妈钱包/收支记录'
        verbose_name_plural = u'妈妈钱包/收支记录列表'
        
    def __unicode__(self):
        return '%s'%self.id
    
    def get_value_display(self):
        return self.value / 100.0
    
    get_value_display.allow_tags = True
    get_value_display.admin_order_field = 'value'
    get_value_display.short_description = u"金额"
    
    @property
    def value_money(self):
        return self.get_value_display() 
    
    @property
    def log_type_name(self):
        return self.get_log_type_display()   
    
    @property
    def carry_type_name(self):
        return self.get_carry_type_display()   
    
    @property
    def status_name(self):
        return self.get_status_display()
    
    
from . import signals

def push_Pending_Carry_To_Cash(obj,*args,**kwargs):
    
    from flashsale.xiaolumm.tasks import task_Push_Pending_Carry_Cash
    
    task_Push_Pending_Carry_Cash.s(xlmm_id=obj)()
    
signals.signal_push_pending_carry_to_cash.connect(push_Pending_Carry_To_Cash,sender=XiaoluMama)


from flashsale.pay.signals import signal_saletrade_pay_confirm
from flashsale.pay.models import SaleTrade

def update_Xlmm_Agency_Progress(obj,*args,**kwargs):
    
    if (obj.status == SaleTrade.WAIT_SELLER_SEND_GOODS 
        and obj.is_Deposite_Order()):
        order_buyer = obj.order_buyer 
        xlmms = XiaoluMama.objects.filter(openid=order_buyer.unionid)
        if xlmms.count() > 0 :
            xlmm = xlmms[0]
            xlmm.progress = XiaoluMama.PAY
            xlmm.save()
            
    
signal_saletrade_pay_confirm.connect(update_Xlmm_Agency_Progress,sender=SaleTrade)

    
    