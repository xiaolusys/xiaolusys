#-*- coding:utf-8 -*-
import datetime
from django.db import models
from django.contrib.auth.models import User as DjangoUser
from shopapp.weixin.models import UserGroup
from .managers import XiaoluMamaManager
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
# Create your models here.
from shopback.items.models import Product
from shopapp.weixin.models_sale import WXProductSku
from common.modelutils import update_model_fields
import logging

logger = logging.getLogger('django.request')
ROI_CLICK_START = datetime.date(2015,8,25)
ORDER_RATEUP_START = datetime.date(2015,7,8)

MM_CLICK_DAY_LIMIT = 1
MM_CLICK_DAY_BASE_COUNT  = 10
MM_CLICK_PER_ORDER_PLUS_COUNT = 50


class XiaoluMama(models.Model):
    
    EFFECT = 'effect'
    FROZEN = 'forzen'
    STATUS_CHOICES = (
        (EFFECT,u'正常'),
        (FROZEN,u'已冻结')
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
    CHARGE_STATUS_CHOICES = (
        (UNCHARGE,u'待接管'),
        (CHARGED,u'已接管'),
        )

    INNER_LEVEL = 1
    VIP_LEVEL = 2
    A_LEVEL = 3

    AGENCY_LEVEL = (
        (INNER_LEVEL, u"内部"),
        (VIP_LEVEL, u"VIP类"),
        (A_LEVEL, u"A类"),
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
    
    hasale  = models.BooleanField(default=False,verbose_name=u"有购买")
    
    agencylevel = models.IntegerField(default=1, choices=AGENCY_LEVEL, verbose_name=u"代理类别")
    target_complete = models.FloatField(default=0.0, verbose_name=u"升级指标完成额")
    user_group  = BigIntegerForeignKey(UserGroup,null=True,verbose_name=u"分组")
    
    charge_time = models.DateTimeField(default=datetime.datetime.now,
                                       db_index=True,blank=True,null=True,verbose_name=u'接管时间')
    
    created  = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')
    modified = models.DateTimeField(auto_now=True,verbose_name=u'修改时间')
    status   = models.CharField(max_length=16,blank=True,choices=STATUS_CHOICES,
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
        """ 妈妈考试是否通过 """
        return True
#         from flashsale.mmexam.models import Result
#         results = Result.objects.filter(daili_user=self.openid)
#         if results.count() > 0  and results[0].is_Exam_Funished():
#             return True
#         return False
    
    def get_Mama_Deposite(self):
        """ 获取妈妈押金金额 """
        agency_levels = AgencyLevel.objects.filter(id=self.agencylevel)
        if agency_levels.count() == 0:
            return 0
        return agency_levels[0].deposit
    
    def get_Mama_Deposite_Amount(self):
        """ 获取妈妈押金对应账户金额 """
        agency_levels = AgencyLevel.objects.filter(id=self.agencylevel)
        if agency_levels.count() == 0:
            return 0
        return agency_levels[0].cash 
    
    def get_Mama_Thousand_Target_Amount(self):
        """ 获取妈妈千元基准成交额 """
        agency_levels = AgencyLevel.objects.filter(id=self.agencylevel)
        if agency_levels.count() == 0:
            return float('Inf')
        return agency_levels[0].target 
    
    def get_Mama_Thousand_Rate(self):
        """ 获取妈妈千元提成率 """
        agency_levels = AgencyLevel.objects.filter(id=self.agencylevel)
        if agency_levels.count() == 0:
            return float('Inf')
        return agency_levels[0].extra_rate_percent()
        
        
    def get_Mama_Agency_Rebeta_Rate(self):
        """ 获取代理妈妈获取子级代理的提成点数 """
        if self.agencylevel > 1:
            return 0.05
        return 0
        
    def get_Mama_Order_Rebeta_Rate(self):
        """ 获取小鹿妈妈订单提成点数 """
        agency_levels = AgencyLevel.objects.filter(id=self.agencylevel)
        if agency_levels.count() == 0:
            return 0
        
        agency_level = agency_levels[0]
        return agency_level.get_Rebeta_Rate()
    
    def get_Mama_Order_Product_Rate(self,product):
        """
        	如果特卖商品detail设置代理了返利，
        	则返回设置值，否则返回小鹿妈妈统一设置值
        """
#         if self.agencylevel != 2:
#             return 0.0
        try:
            pdetail = product.details
        except:
            return self.get_Mama_Order_Rebeta_Rate()
        else:
            rate = pdetail.mama_rebeta_rate()
            if rate is None:
                return self.get_Mama_Order_Rebeta_Rate()
            return rate
        
    def get_Mama_Order_Rebeta(self,order):
        #如果订单来自小鹿特卖平台
        if hasattr(order,'item_id'):
            product_qs = Product.objects.filter(id=order.item_id)
        #如果订单来自微信小店
        elif hasattr(order,'product_sku'):
            try:
                wxsku =  WXProductSku.objects.get(sku_id=order.product_sku,
            									  product=order.product_id)
                product_qs = Product.objects.filter(outer_id=wxsku.outer_id) 
            except Exception,exc:
                logger.error(exc.message,exc_info=True)
                product_qs = Product.objects.none()
        else:
            product_qs = Product.objects.none()
            
        product_ins = product_qs.count() > 0 and product_qs[0] or None
        rebeta_rate = self.get_Mama_Order_Product_Rate(product_ins)
        
        order_price = 0
        if hasattr(order,'order_total_price'):
            order_price = order.order_total_price
        elif hasattr(order,'payment'):
            order_price = int(order.payment * 100)
        
        return rebeta_rate * order_price
    
    
    def get_Mama_Order_Amount(self,order):
        #如果订单来自小鹿特卖平台
        order_price = 0
        if hasattr(order,'order_total_price'):
            order_price = order.order_total_price
        elif hasattr(order,'payment'):
            order_price = int(order.payment * 100)
        return order_price

    def get_Mama_Trade_Rebeta(self,trade):
        """ 获取妈妈交易返利提成 """
        if hasattr(trade,'normal_orders'):
            rebeta = 0
            for order in trade.normal_orders:
                rebeta += self.get_Mama_Order_Rebeta(order)
            return rebeta
        return 	self.get_Mama_Order_Rebeta(trade)
    
    def get_Mama_Trade_Amount(self,trade):
        """ 获取妈妈交易返利提成 """
        if hasattr(trade,'normal_orders'):
            amount = 0
            for order in trade.normal_orders:
                if self.get_Mama_Order_Rebeta(order) == 0:
                    continue
                amount += self.get_Mama_Order_Amount(order)
            return amount
        if self.get_Mama_Order_Rebeta(trade) == 0:
            return 0
        return self.get_Mama_Order_Amount(trade)
    
    def get_Mama_Click_Price(self,ordernum):
        """ 获取今日小鹿妈妈点击价格 """
        cur_date = datetime.date.today() 
        return self.get_Mama_Click_Price_By_Day(ordernum,day_date=cur_date)
    
    def get_Mama_Click_Price_By_Day(self, ordernum, day_date=None):
        """ 按日期获取小鹿妈妈点击价格 """
        if self.agencylevel < 2:
            return 0
        if day_date >= ROI_CLICK_START:
            return 10
        return 0
#         agency_level = agency_levels[0]
#         if not day_date or day_date < ROI_CLICK_START:
#             return base_price + agency_level.get_Click_Price(ordernum)
#         
#         return 0
        
#         pre_date = day_date - datetime.timedelta(days=1)
#         mm_stats = MamaDayStats.objects.filter(xlmm=self.id,day_date=pre_date)
#         if mm_stats.count() > 0:
#             base_price = mm_stats[0].base_click_price
#         
#         return base_price + agency_level.get_Click_Price(ordernum)
    
        
    def get_Mama_Max_Valid_Clickcount(self,ordernum):
        """ 获取小鹿妈妈最大有效点击数 """
        agency_levels = AgencyLevel.objects.filter(id=self.agencylevel)
        if agency_levels.count() == 0:
            return 0
        agency_level = agency_levels[0]
        return agency_level.get_Max_Valid_Clickcount(ordernum)
    
    
    def push_carrylog_to_cash(self,clog):
        
        if self.id != clog.xlmm:
            raise Exception(u'现金日志与妈妈编号不匹配') 
        
        try:
            clog = CarryLog.objects.get(id=clog.id,status=CarryLog.PENDING)
        except CarryLog.DoesNotExist:
            raise Exception(u'妈妈收支记录重复确认:%s'%clog.id)

        clog.status = CarryLog.CONFIRMED
        clog.save()
        
        if clog.carry_type == CarryLog.CARRY_IN:
            self.cash = models.F('cash') + clog.value
            self.pending = models.F('pending') - clog.value
        else:
            self.cash = models.F('cash') - clog.value
        update_model_fields(self,update_fields=['cash','pending'])
        
        
# from .clickprice import CLICK_TIME_PRICE

class AgencyLevel(models.Model):
    
    category = models.CharField(max_length=11,unique=True,blank=False,verbose_name=u"类别")
    deposit  = models.IntegerField(default=0,verbose_name=u"押金(元)")
    cash     = models.IntegerField(default=0,verbose_name=u"现金(元)")
    basic_rate = models.IntegerField(default=0,verbose_name=u"基本佣金率（百分比）")
    target     = models.IntegerField(default=0,verbose_name=u"达标额度（元）")
    extra_rate = models.IntegerField(default=0,verbose_name=u"奖励佣金率（百分比）")
    created    = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')

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
    
    def extra_rate_percent(self):
        return self.get_extra_rate_display()
    
    def get_Click_Price(self,order_num):
        """ 点击据订单价格提成 """
        if self.id < 2:
            return 0
        return 0
#         click_price = 0
#         if order_num > 2:
#             click_price = 0.3
#         else:
#             click_price += order_num * 0.1
#         
#         return click_price * 100
    
    def get_Max_Valid_Clickcount(self,order_num):
        return MM_CLICK_DAY_BASE_COUNT + MM_CLICK_PER_ORDER_PLUS_COUNT * order_num
        
    
    def get_Rebeta_Rate(self,*args,**kwargs):
        
        today = datetime.date.today()
        if today > ORDER_RATEUP_START:
            return self.basic_rate / 100.0
        return (self.basic_rate / 100.0) / 2
    

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

from django.db.models.signals import post_save


def Create_Or_Change_Clickcount(sender, instance, created, **kwargs):
    from flashsale.clickcount.tasks import task_Count_ClickCount_Info
    task_Count_ClickCount_Info.s(instance, created)()

post_save.connect(Create_Or_Change_Clickcount, sender=Clicks)

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
    get_value_display.short_description = u"提现金额"
    
    @property
    def value_money(self):
        return self.get_value_display()    
    


class CarryLog(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELED = 'canceled'

    STATUS_CHOICES = (
        (PENDING,u'待确认'),
        (CONFIRMED,u'已确定'),
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
    MAMA_RECRUIT   = 'recruit'
    ORDER_RED_PAC = 'ordred'
    
    LOG_TYPE_CHOICES = (
        (ORDER_REBETA,u'订单返利'),
        (ORDER_BUY,u'消费支出'),
        (REFUND_RETURN,u'退款返现'),
        (CLICK_REBETA,u'点击兑现'),
        (CASH_OUT,u'钱包提现'),
        (DEPOSIT,u'押金'),
        (THOUSAND_REBETA,u'千元提成'),
        (AGENCY_SUBSIDY,u'代理补贴'),
        (MAMA_RECRUIT,u'招募奖金'),
        (ORDER_RED_PAC,u'订单红包')
    )
    
    CARRY_OUT = 'out'
    CARRY_IN  = 'in'
    CARRY_TYPE_CHOICES = (
        (CARRY_OUT,u'支出'),
        (CARRY_IN,u'收入'),
    )
    
    xlmm       = models.BigIntegerField(default=0,db_index=True,verbose_name=u"妈妈编号")
    order_num  = models.BigIntegerField(default=0,db_index=True,verbose_name=u"记录标识")
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
    
    from flashsale.xiaolumm import tasks 
    #更新提成金额
    tasks.task_Push_Pending_Carry_Cash.s(xlmm_id=obj)()
    
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
            update_model_fields(xlmm,update_fields=['progress'])
            
signal_saletrade_pay_confirm.connect(update_Xlmm_Agency_Progress,sender=SaleTrade)

# 首单红包，10单红包

class OrderRedPacket(models.Model):
    
    xlmm = models.IntegerField(unique=True, blank=False, verbose_name=u"妈妈编号")
    first_red = models.BooleanField(default=False, verbose_name=u"首单红包")
    ten_order_red = models.BooleanField(default=False, verbose_name=u"十单红包")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')

    class Meta:
        db_table = 'xiaolumm_order_red_packet'
        verbose_name = u'妈妈订单红包表'
        verbose_name_plural = u'妈妈订单红包列表'


class MamaDayStats(models.Model):
    
    xlmm        = models.IntegerField(default=0, verbose_name=u'妈妈编号')
    day_date    = models.DateField(verbose_name=u'统计日期')
    base_click_price  = models.IntegerField(default=0,verbose_name=u'基础点击价格')
    
    lweek_clicks = models.IntegerField(default=0,verbose_name=u'周有效点击')
    lweek_buyers = models.IntegerField(default=0,verbose_name=u'周购买用户')
    lweek_payment = models.IntegerField(default=0,verbose_name=u'周购买金额')
    
    tweek_clicks = models.IntegerField(default=0,verbose_name=u'两周有效点击')
    tweek_buyers = models.IntegerField(default=0,verbose_name=u'两周购买用户')
    tweek_payment = models.IntegerField(default=0,verbose_name=u'两周购买金额')
    
    class Meta:
        db_table = 'xiaolumm_dailystat'
        unique_together = ('xlmm', 'day_date') 
        app_label = 'xiaolumm'
        verbose_name = u'妈妈/每日统计'
        verbose_name_plural = u'妈妈/每日统计列表'
    
    def get_base_click_price_display(self):
        return self.base_click_price / 100.0
    
    get_base_click_price_display.allow_tags = True
    get_base_click_price_display.admin_order_field = 'base_click_price'
    get_base_click_price_display.short_description = u"基础点击价格"
    
    def get_lweek_payment_display(self):
        return self.lweek_payment / 100.0
    
    get_lweek_payment_display.allow_tags = True
    get_lweek_payment_display.admin_order_field = 'lweek_payment'
    get_lweek_payment_display.short_description = u"周购买金额"
    
    def get_tweek_payment_display(self):
        return self.tweek_payment / 100.0
    
    get_tweek_payment_display.allow_tags = True
    get_tweek_payment_display.admin_order_field = 'tweek_payment'
    get_tweek_payment_display.short_description = u"两周购买金额"
    
    @property
    def lweek_roi(self):
        if self.lweek_clicks == 0:
            return 0
        return float('%.4f'%(self.lweek_buyers / (self.lweek_clicks * 1.0)))
        
    def get_lweek_roi_display(self):
        return self.lweek_roi

    get_lweek_roi_display.allow_tags = True
    get_lweek_roi_display.short_description = u"周转化率"
    
    @property
    def tweek_roi(self):
        if self.tweek_clicks == 0:
            return 0
        return float('%.4f'%(self.tweek_buyers / (self.tweek_clicks * 1.0)))
        
    def get_tweek_roi_display(self):
        return self.tweek_roi

    get_tweek_roi_display.allow_tags = True
    get_tweek_roi_display.short_description = u"两周转化率"
    
    def calc_click_price(self):
        
        if self.lweek_clicks < 50:
            return 20
        
        xlmm = XiaoluMama.objects.get(id=self.xlmm)
        if not xlmm.charge_time:
            return 0
        #如果代理接管时间少于一周，点击价格为0.2元
        delta_days = (datetime.datetime.now() - xlmm.charge_time).days
        if delta_days < 5:
            return 20
        #如果两周连续转化率为0
        if delta_days > 7 and self.tweek_clicks > 99 and self.tweek_roi == 0:
            return 1
        #如果一周转化率为0
        if self.lweek_roi == 0:
            return 10
        
        return 20











