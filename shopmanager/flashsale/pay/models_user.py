#-*- coding:utf-8 -*-
import random
import datetime
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User as DjangoUser
    
from core.fields import BigIntegerAutoField,BigIntegerForeignKey
from .base import PayBaseModel
from flashsale.pay.models_envelope import Envelop
from shopback.base import log_action, ADDITION, CHANGE
import constants
from shopapp.weixin.models import WeixinUnionID


class Register(PayBaseModel):
    
    MAX_VALID_COUNT   = 6
    MAX_SUBMIT_TIMES  = 20
    
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
    
    INACTIVE = 0   #未激活
    NORMAL = 1     #正常
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
    
    def is_loginable(self):
        return self.status == self.NORMAL
    
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
        
    def get_openid_and_unoinid_by_appkey(self,appkey):
        if not self.unionid.strip():
            return ('','')
        from shopapp.weixin import options
        openid = options.get_openid_by_unionid(self.unionid,appkey)
        if not openid and appkey == settings.WXPAY_APPID:
            return self.openid, self.unionid
        return openid, self.unionid

    def getBudget(self):
        """特卖用户钱包"""
        try:
            budget = UserBudget.objects.get(user_id=self.id)
            return budget
        except UserBudget.DoesNotExist:
            return None

class UserBudget(PayBaseModel):
    """ 特卖用户钱包 """
    class Meta:
        db_table = 'flashsale_userbudget'
        verbose_name=u'特卖/用户钱包'
        verbose_name_plural = u'特卖/用户钱包列表'
    
    user        = models.OneToOneField(Customer,verbose_name= u'原始用户')
    amount      = models.IntegerField(default=0,verbose_name=u'账户余额(分)')
    
    total_redenvelope = models.CharField(max_length=32,blank=True,verbose_name=u'累计获取红包')
    total_consumption = models.CharField(max_length=32,blank=True,verbose_name=u'累计消费') 
    total_refund      = models.CharField(max_length=32,blank=True,verbose_name=u'累计退款') 
    
    def __unicode__(self):
        return u'<%s,%s>'%(self.user, self.amount)

    def get_amount_display(self):
        """ 返回金额　"""
        return self.amount / 100.0

    def action_budget_cashout(self, cash_out_amount):
        """
        用户钱包提现
        cash_out_amount　整型　以分为单位
        """
        code = 0
        if not isinstance(cash_out_amount, int):  # 参数类型错误(如果不是整型)
            code = 3
            return code
        # 如果提现金额小于0　code 1
        if cash_out_amount < 0:
            code = 1
        # 如果提现金额大于当前用户钱包的金额 code 2
        elif cash_out_amount > self.amount:
            code = 2
        # 提现操作
        else:
            # 提现前金额
            try:
                wx_union = WeixinUnionID.objects.get(app_key=settings.WXPAY_APPID, unionid=self.user.unionid)
            except WeixinUnionID.DoesNotExist:
                code = 4  # 用户没有公众号提现账户
                return code
            before_cash_amount = self.amount
            # 减去当前用户的账户余额
            amount = self.amount - cash_out_amount
            self.amount = amount
            self.save()  # 保存提现后金额
            # 创建钱包提现记录
            budgelog = BudgetLog.objects.create(customer_id=self.user.id,
                                                flow_amount=cash_out_amount,
                                                budget_type=BudgetLog.BUDGET_OUT,
                                                budget_log_type=BudgetLog.BG_CASHOUT,
                                                budget_date=datetime.date.today(),
                                                status=BudgetLog.CONFIRMED)
            # 发放公众号红包
            recipient = wx_union.openid  # 接收人的openid
            body = constants.ENVELOP_BODY  # 红包祝福语
            description = constants.ENVELOP_CASHOUT_DESC.format(self.user.id,
                                                                before_cash_amount)  # 备注信息 用户id, 提现前金额
            Envelop.objects.create(amount=cash_out_amount,
                                   platform=Envelop.XLMMAPP,
                                   recipient=recipient,
                                   subject=Envelop.XLAPP_CASHOUT,
                                   body=body,
                                   description=description,
                                   referal_id=budgelog.id)
            log_action(self.user.user.id, self, CHANGE, u'用户提现')
        return code

    
class BudgetLog(PayBaseModel):
    """ 特卖用户钱包记录 """
    class Meta:
        db_table = 'flashsale_userbudgetlog'
        verbose_name=u'特卖/用户钱包收支记录'
        verbose_name_plural = u'特卖/用户钱包收支记录'
    
    BUDGET_IN  = 0
    BUDGET_OUT = 1
    
    BUDGET_CHOICES = (
        (BUDGET_IN,u'收入'),
        (BUDGET_OUT,u'支出'),
    )
    
    BG_ENVELOPE = 'envelop'
    BG_REFUND   = 'refund'
    BG_CONSUM   = 'consum'
    BG_CASHOUT  = 'cashout'
    
    BUDGET_LOG_CHOICES = (
        (BG_ENVELOPE,u'红包'),
        (BG_REFUND,u'退款'),
        (BG_CONSUM,u'消费'),
        (BG_CASHOUT,u'提现'),
    )
    
    CONFIRMED = 0
    CANCELED  = 1

    STATUS_CHOICES = (
        (CONFIRMED,u'已确定'),
        (CANCELED,u'已取消'),
    )
    
    customer_id = models.BigIntegerField(db_index=True, verbose_name=u'用户id')
    flow_amount = models.IntegerField(default=0,verbose_name=u'流水金额(分)')
    budget_type = models.IntegerField(choices=BUDGET_CHOICES,db_index=True,null=False,verbose_name=u"收支类型")
    budget_log_type = models.CharField(max_length=8,choices=BUDGET_LOG_CHOICES,db_index=True,null=False,verbose_name=u"记录类型")
    budget_date = models.DateField(default=datetime.date.today,verbose_name=u'业务日期')
    status     = models.IntegerField(choices=STATUS_CHOICES, db_index=True, default=CONFIRMED, verbose_name=u'状态')

    def __unicode__(self):
        return u'<%s,%s>' % (self.customer_id, self.flow_amount)

    def get_flow_amount_display(self):
        """ 返回金额　"""
        return self.flow_amount / 100.0
    
    