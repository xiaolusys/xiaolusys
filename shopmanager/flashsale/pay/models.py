#-*- coding:utf-8 -*-
import uuid
import datetime
from django.db import models
from django.shortcuts import get_object_or_404
from django.db.models.signals import post_save
from django.db import transaction

from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
from .base import PayBaseModel, BaseModel
from shopback.logistics.models import LogisticsCompany
from shopback.items.models import DIPOSITE_CODE_PREFIX
from .models_user import Register,Customer,UserBudget,BudgetLog
from .models_addr import District,UserAddress
from .models_custom import Productdetail,GoodShelf,ModelProduct,ActivityEntry
from .models_refund import SaleRefund
from .models_envelope import Envelop
from .models_coupon import Integral,IntegralLog
from .models_coupon_new import UserCoupon, CouponsPool, CouponTemplate
from .models_share import CustomShare
from . import managers

from .signals import signal_saletrade_pay_confirm
from .options import uniqid
from core.fields import JSONCharMyField
from core.options import log_action, ADDITION, CHANGE
from common.utils import update_model_fields
import logging

logger = logging.getLogger('django.request')

FLASH_SELLER_ID  = 'flashsale'
AGENCY_DIPOSITE_CODE = DIPOSITE_CODE_PREFIX
TIME_FOR_PAYMENT = 25 * 60


def genUUID():
    return str(uuid.uuid1(clock_seq=True))

def genTradeUniqueid():
    return uniqid('%s%s'%(SaleTrade.PREFIX_NO,datetime.date.today().strftime('%y%m%d')))

class SaleTrade(BaseModel):
    """ payment (实付金额) = total_fee (商品总金额) + post_fee (邮费) - discount_fee (优惠金额) """
    PREFIX_NO  = 'xd'
    WX         = 'wx'
    ALIPAY     = 'alipay'
    WX_PUB     = 'wx_pub'
    ALIPAY_WAP = 'alipay_wap'
    UPMP_WAP   = 'upmp_wap'
    WALLET     = 'wallet'
    BUDGET     = 'budget'
    APPLE      = 'applepay_upacp'
    CHANNEL_CHOICES = (
        (BUDGET,u'小鹿钱包'),
        (WALLET,u'妈妈钱包'),
        (WX,u'微信APP'),
        (ALIPAY,u'支付宝APP'),
        (WX_PUB,u'微支付'),
        (ALIPAY_WAP,u'支付宝'),
        (UPMP_WAP,u'银联'),
        (APPLE,u'ApplePay'),
    )
    
    PREPAY  = 0
    POSTPAY = 1
    TRADE_TYPE_CHOICES = (
        (PREPAY,u"在线支付"),
        (POSTPAY,"货到付款"),
    )
    
    SALE_ORDER     = 0
    RESERVE_ORDER  = 1
    DEPOSITE_ORDER = 2
    ORDER_TYPE_CHOICES = (
        (SALE_ORDER,u"特卖订单"),
        (RESERVE_ORDER,"预订制"),
        (DEPOSITE_ORDER,"押金订单"),
    )
    
    
    TRADE_NO_CREATE_PAY = 0
    WAIT_BUYER_PAY = 1
    WAIT_SELLER_SEND_GOODS = 2
    WAIT_BUYER_CONFIRM_GOODS = 3
    TRADE_BUYER_SIGNED = 4
    TRADE_FINISHED = 5
    TRADE_CLOSED = 6
    TRADE_CLOSED_BY_SYS = 7
    NORMAL_TRADE_STATUS = (WAIT_BUYER_PAY,
                           WAIT_SELLER_SEND_GOODS,
                           WAIT_BUYER_CONFIRM_GOODS,
                           TRADE_BUYER_SIGNED,
                           TRADE_FINISHED,
                           TRADE_CLOSED,
                           TRADE_CLOSED_BY_SYS)
    
    REFUNDABLE_STATUS = (WAIT_SELLER_SEND_GOODS,
                         WAIT_BUYER_CONFIRM_GOODS)
    
    INGOOD_STATUS = (WAIT_SELLER_SEND_GOODS,
                     WAIT_BUYER_CONFIRM_GOODS,
                     TRADE_BUYER_SIGNED,
                     TRADE_FINISHED)
    
    TRADE_STATUS = (
        (TRADE_NO_CREATE_PAY,u'订单创建'),
        (WAIT_BUYER_PAY,u'待付款'),
        (WAIT_SELLER_SEND_GOODS,u'已付款'),
        (WAIT_BUYER_CONFIRM_GOODS,u'已发货'),
        (TRADE_BUYER_SIGNED,u'确认签收'),
        (TRADE_FINISHED,u'交易成功'),
        (TRADE_CLOSED,u'退款关闭'),
        (TRADE_CLOSED_BY_SYS,u'交易关闭'),
    )

    id    = BigIntegerAutoField(primary_key=True,verbose_name=u'订单ID')
    
    tid   = models.CharField(max_length=40,unique=True,
                             default=genTradeUniqueid,
                             verbose_name=u'原单ID')
    buyer_id    = models.BigIntegerField(null=False,db_index=True,verbose_name=u'买家ID')
    buyer_nick  = models.CharField(max_length=64,blank=True,verbose_name=u'买家昵称')
    
    channel     = models.CharField(max_length=16,db_index=True,
                                   choices=CHANNEL_CHOICES,blank=True,verbose_name=u'付款方式')
    
    payment    =   models.FloatField(default=0.0,verbose_name=u'实付款')
    post_fee   =   models.FloatField(default=0.0,verbose_name=u'物流费用')
    discount_fee  =   models.FloatField(default=0.0,verbose_name=u'优惠折扣')
    total_fee  =   models.FloatField(default=0.0,verbose_name=u'总费用')
    
    buyer_message = models.TextField(max_length=1000,blank=True,verbose_name=u'买家留言')
    seller_memo   = models.TextField(max_length=1000,blank=True,verbose_name=u'卖家备注')
    
    pay_time     = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'付款日期')
    consign_time = models.DateTimeField(null=True,blank=True,verbose_name=u'发货日期')
    
    trade_type = models.IntegerField(choices=TRADE_TYPE_CHOICES,default=PREPAY,verbose_name=u'交易类型')
    order_type = models.IntegerField(choices=ORDER_TYPE_CHOICES,default=SALE_ORDER,verbose_name=u'订单类型')
    
    out_sid         = models.CharField(max_length=64,blank=True,verbose_name=u'物流编号')
    logistics_company  = models.ForeignKey(LogisticsCompany,null=True,
                                           blank=True,verbose_name=u'物流公司')
    receiver_name    =  models.CharField(max_length=25,
                                         blank=True,verbose_name=u'收货人姓名')
    receiver_state   =  models.CharField(max_length=16,blank=True,verbose_name=u'省')
    receiver_city    =  models.CharField(max_length=16,blank=True,verbose_name=u'市')
    receiver_district  =  models.CharField(max_length=16,blank=True,verbose_name=u'区')
    
    receiver_address   =  models.CharField(max_length=128,blank=True,verbose_name=u'详细地址')
    receiver_zip       =  models.CharField(max_length=10,blank=True,verbose_name=u'邮编')
    receiver_mobile    =  models.CharField(max_length=11,db_index=True,blank=True,verbose_name=u'手机')
    receiver_phone     =  models.CharField(max_length=20,blank=True,verbose_name=u'电话')

    openid  = models.CharField(max_length=40,blank=True,verbose_name=u'微信OpenID')
    charge  = models.CharField(max_length=28,verbose_name=u'支付编号')
    
    extras_info  = JSONCharMyField(max_length=256, blank=True, default={}, verbose_name=u'附加信息')
    
    status  = models.IntegerField(choices=TRADE_STATUS,default=TRADE_NO_CREATE_PAY,
                              db_index=True,blank=True,verbose_name=u'交易状态')
    
#     is_part_consign  = models.BooleanField(db_index=True,default=False,verbose_name=u'分单发货')
#     consign_parmas   = JSONCharMyField(max_length=512, blank=True, default='[]', verbose_name=u'发货信息')
    objects = models.Manager()
    normal_objects = managers.NormalSaleTradeManager()
    class Meta:
        db_table = 'flashsale_trade'
        verbose_name=u'特卖/订单'
        verbose_name_plural = u'特卖/订单列表'

    def __unicode__(self):
        return '<%s,%s>'%(str(self.id),self.buyer_nick)
    
    @property
    def normal_orders(self):
        return self.sale_orders.filter(status__in=SaleOrder.NORMAL_ORDER_STATUS)
    
    @property
    def order_title(self):
        if self.sale_orders.count() > 0:
            return self.sale_orders.all()[0].title
        return ''
    
    @property
    def order_num(self):
        onum = 0
        order_values = self.sale_orders.values_list('num')
        for order in order_values:
            onum += order[0]
        return onum
    
    @property
    def order_pic(self):
        if self.sale_orders.count() > 0:
            return self.sale_orders.all()[0].pic_path
        return ''
    
    @property
    def status_name(self):
        return self.get_status_display()
    
    @property
    def body_describe(self):
        subc = ''
        for order in self.sale_orders.all():
            subc += order.title
        return subc
    
    @property
    def order_buyer(self):
        return Customer.objects.get(id=self.buyer_id)
    
    def get_buyer_openid(self):
        """ 获取订单用户openid """
        if self.openid:
            return self.openid
        return self.order_buyer.openid
    
    @classmethod
    def mapTradeStatus(cls,index):
        from shopback.trades.models import MergeTrade
        status_list = MergeTrade.TAOBAO_TRADE_STATUS
        return status_list[index][0]

    def is_paid_via_app(self):
        """
        Roughly check whether order is paid via app, should be revised later.
        """
        return self.channel == SaleTrade.WX or self.channel == SaleTrade.ALIPAY
    
    def is_payable(self):
        now = datetime.datetime.now()
        return self.status == self.WAIT_BUYER_PAY and (now - self.created).seconds < TIME_FOR_PAYMENT
    
    def is_closed(self):
        return self.status == self.TRADE_CLOSED_BY_SYS
    
    def is_refunded(self):
        return self.status == self.TRADE_CLOSED
    
    def is_Deposite_Order(self):
        
        
        for order in self.sale_orders.all():
            if order.outer_id.startswith(AGENCY_DIPOSITE_CODE):
                return True
        return False
    
    def is_wallet_paid(self):
        return self.channel == self.WALLET
    
    def release_lock_skunum(self):
        try:
            for order in self.normal_orders:
                product_sku = ProductSku.objects.get(id=order.sku_id)
                Product.objects.releaseLockQuantity(product_sku, order.num)
        except Exception,exc:
            logger = logging.getLogger('django.request')
            logger.error(exc.message,exc_info=True)
    
    def increase_lock_skunum(self):
        try:
            for order in self.normal_orders:
                product_sku = ProductSku.objects.get(id=order.sku_id)
                Product.objects.lockQuantity(product_sku, order.num)
        except Exception,exc:
            logger = logging.getLogger('django.request')
            logger.error(exc.message,exc_info=True)
    
    def confirm_payment(self):
        from django_statsd.clients import statsd
        statsd.incr('xiaolumm.postpay_count')
        statsd.incr('xiaolumm.postpay_amount',self.payment)
        signal_saletrade_pay_confirm.send(sender=SaleTrade,obj=self)
            
    def charge_confirm(self,charge_time=None):
        """ 如果付款期间，订单被订单号任务关闭则不减锁定数量 """
        trade_close = self.is_closed()
        self.status = self.WAIT_SELLER_SEND_GOODS
        self.pay_time = charge_time or datetime.datetime.now()
        update_model_fields(self,update_fields=['status','pay_time'])
        
        for order in self.sale_orders.all():
            order.status   = order.WAIT_SELLER_SEND_GOODS
            order.pay_time = self.pay_time
            order.save()
        #付款后订单被关闭，则加上锁定数
        if trade_close:
            self.increase_lock_skunum() 
        self.confirm_payment()
    
    @transaction.commit_on_success
    def close_trade(self):
        """ 关闭待付款订单 """
        try:
            SaleTrade.objects.get(id=self.id,status=SaleTrade.WAIT_BUYER_PAY)
        except SaleTrade.DoesNotExist:
            return
        self.status = SaleTrade.TRADE_CLOSED_BY_SYS
        self.save()
        
        for order in self.normal_orders:
            order.close_order()
        #释放被当前订单使用的优惠券
        self.release_coupon()
        
    def release_coupon(self):
        """ 释放订单对应的优惠券 """
        UserCoupon.objects.filter(sale_trade=self.id, 
                                  status=UserCoupon.USED
                                  ).update(status=UserCoupon.UNUSED)
    
    @property
    def unsign_orders(self):
        """ 允许签收的订单 （已经付款、已发货、货到付款签收）"""
        return self.sale_orders.filter(status__in=
                                       (SaleOrder.WAIT_SELLER_SEND_GOODS,
                                       SaleOrder.WAIT_BUYER_CONFIRM_GOODS,
                                       SaleOrder.TRADE_BUYER_SIGNED))

    def confirm_sign_trade(self):
        """确认签收 修改该交易 状态到交易完成 """
        SaleTrade.objects.get(id=self.id)
        for order in self.unsign_orders:
            order.confirm_sign_order()  # 同时修改正常订单到交易完成
        self.status = SaleTrade.TRADE_FINISHED
        self.save()


def record_supplier_args(sender, obj, **kwargs):
    """ 随支付成功信号　更新供应商的销售额，　销售数量
        :arg obj -> SaleTrade instance
        :except None
        :return None
    """
    normal_orders = obj.normal_orders.all()
    for order in normal_orders:
        item_id = order.item_id
        pro = Product.objects.get(id=item_id)
        sal_p, supplier = pro.pro_sale_supplier()
        if supplier is not None:
            supplier.total_sale_num = F('total_sale_num') + order.num
            supplier.total_sale_amount = F("total_sale_amount") + order.payment
            update_model_fields(supplier, update_fields=['total_sale_num', 'total_sale_amount'])


signal_saletrade_pay_confirm.connect(record_supplier_args, sender=SaleTrade)

from shopback.categorys.models import CategorySaleStat


def category_trade_stat(sender, obj, **kwargs):
    """
        记录不同类别产品的销售数量和销售金额
    """
    orders = obj.sale_orders.all()
    for order in orders:
        try:
            pro = Product.objects.get(id=order.item_id)
            cgysta, state = CategorySaleStat.objects.get_or_create(stat_date=pro.sale_time, 
                                                                   category=pro.category.cid)
            if state:  # 如果是新建
                cgysta.sale_amount = order.payment  # 销售金额
                cgysta.sale_num = order.num  # 销售数量
            else:  # 在原有基础上面加销售数量和销售金额
                cgysta.sale_amount = F("sale_amount") + order.payment
                cgysta.sale_num = F("sale_num") + order.num
            update_model_fields(cgysta, update_fields=["sale_amount", "sale_num"])
        except Exception,exc:
            logger.error(exc.message,exc_info=True)

signal_saletrade_pay_confirm.connect(category_trade_stat, sender=SaleTrade)


class SaleOrder(PayBaseModel):
    """ 特卖订单明细 """
    class Meta:
        db_table = 'flashsale_order'
        verbose_name=u'特卖/订单明细'
        verbose_name_plural = u'特卖/订单明细列表'
    
    PREFIX_NO  = 'xo'
    TRADE_NO_CREATE_PAY = 0
    WAIT_BUYER_PAY = 1
    WAIT_SELLER_SEND_GOODS = 2
    WAIT_BUYER_CONFIRM_GOODS = 3
    TRADE_BUYER_SIGNED = 4
    TRADE_FINISHED = 5
    TRADE_CLOSED = 6
    TRADE_CLOSED_BY_SYS = 7
    ORDER_STATUS = (
        (TRADE_NO_CREATE_PAY,u'订单创建'),
        (WAIT_BUYER_PAY,u'待付款'),
        (WAIT_SELLER_SEND_GOODS,u'已付款'),
        (WAIT_BUYER_CONFIRM_GOODS,u'已发货'),
        (TRADE_BUYER_SIGNED,u'确认签收'),
        (TRADE_FINISHED,u'交易成功'),
        (TRADE_CLOSED,u'退款关闭'),
        (TRADE_CLOSED_BY_SYS,u'交易关闭'),
    )
    
    NORMAL_ORDER_STATUS = (WAIT_BUYER_PAY,
                           WAIT_SELLER_SEND_GOODS,
                           WAIT_BUYER_CONFIRM_GOODS,
                           TRADE_BUYER_SIGNED,
                           TRADE_FINISHED,)
    
    id    = BigIntegerAutoField(primary_key=True)
    oid   = models.CharField(max_length=40,unique=True,
                             default=lambda:uniqid('%s%s'%(SaleOrder.PREFIX_NO,datetime.date.today().strftime('%y%m%d'))),
                             verbose_name=u'原单ID')
    sale_trade = BigIntegerForeignKey(SaleTrade,related_name='sale_orders',
                                       verbose_name=u'所属订单')
    
    item_id  = models.CharField(max_length=64,blank=True,verbose_name=u'商品ID')
    title  =  models.CharField(max_length=128,blank=True,verbose_name=u'商品标题')
    price  = models.FloatField(default=0.0,verbose_name=u'商品单价')

    sku_id = models.CharField(max_length=20,blank=True,verbose_name=u'属性编码')
    num = models.IntegerField(null=True,default=0,verbose_name=u'商品数量')
    
    outer_id = models.CharField(max_length=64,blank=True,verbose_name=u'商品外部编码')
    outer_sku_id = models.CharField(max_length=20,blank=True,verbose_name=u'规格外部编码')
    
    total_fee    = models.FloatField(default=0.0,verbose_name=u'总费用')
    payment      = models.FloatField(default=0.0,verbose_name=u'实付款')
    discount_fee = models.FloatField(default=0.0,verbose_name=u'优惠金额')
    
    sku_name = models.CharField(max_length=256,blank=True,
                                           verbose_name=u'购买规格')
    pic_path = models.CharField(max_length=512,blank=True,verbose_name=u'商品图片')
    
    pay_time      =  models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'付款日期')
    consign_time  =  models.DateTimeField(null=True,blank=True,verbose_name=u'发货日期')
    sign_time     =  models.DateTimeField(null=True,blank=True,verbose_name=u'签收日期')
    
    refund_id     = models.BigIntegerField(null=True,verbose_name=u'退款ID')
    refund_fee    = models.FloatField(default=0.0,verbose_name=u'退款费用')
    refund_status = models.IntegerField(choices=SaleRefund.REFUND_STATUS,
                                       default=SaleRefund.NO_REFUND,
                                       blank=True,verbose_name='退款状态')
    
    status = models.IntegerField(choices=ORDER_STATUS,default=TRADE_NO_CREATE_PAY,
                              db_index=True,blank=True,verbose_name=u'订单状态')
    
        
    def __unicode__(self):
        return '<%s>'%(self.id)

    @property
    def refund(self):
        try:
            refund = SaleRefund.objects.get(trade_id=self.sale_trade.id,order_id=self.id)
            return refund
        except:
            return None
        
    @property
    def refundable(self):
        return self.sale_trade.status in SaleTrade.REFUNDABLE_STATUS
    
    def is_finishable(self):
        """
        1，订单发货后超过15天未确认签收,系统自动变成已完成状态；
        2，订单确认签收后，７天之后订单状态变成已完成；
        """
        now_time = datetime.datetime.now()
        consign_time = self.consign_time
        sign_time = self.sign_time
        if self.refund_status in SaleRefund.REFUNDABLE_STATUS:
            return False
        if (self.status == self.WAIT_BUYER_CONFIRM_GOODS 
            and (not consign_time or (now_time - consign_time).days > 15)):
            return True
        elif (self.status == self.TRADE_BUYER_SIGNED 
            and (not sign_time or (now_time - sign_time).days > 7)):
            return True
        return False
            
    def close_order(self):
        """ 待付款关闭订单 """
        try:
            SaleOrder.objects.get(id=self.id,status=SaleOrder.WAIT_BUYER_PAY)
        except SaleOrder.DoesNotExist,exc:
            return
    
        self.status = self.TRADE_CLOSED_BY_SYS
        self.save()
        sku = get_object_or_404(ProductSku, pk=self.sku_id)
        Product.objects.releaseLockQuantity(sku,self.num)

    def confirm_sign_order(self):
        """确认签收 修改该订单状态到 确认签收状态"""
        self.status = self.TRADE_BUYER_SIGNED
        self.sign_time = datetime.datetime.now()
        self.save()
        
        sale_trade    = self.sale_trade
        normal_orders = sale_trade.normal_orders
        sign_orders   = sale_trade.sale_orders.filter(status=SaleOrder.TRADE_BUYER_SIGNED)
        if sign_orders.count() == normal_orders.count():
            sale_trade.status = SaleTrade.TRADE_BUYER_SIGNED
            update_model_fields(sale_trade,update_fields=['status'])
    
    def second_kill_title(self):
        """ 判断是否秒杀标题　"""
        return True if self.title.startswith(u'秒杀') else False
    
    def is_pending(self):
        return self.status < SaleOrder.TRADE_FINISHED and \
            self.status >= SaleOrder.WAIT_SELLER_SEND_GOODS and \
            self.refund_status <= SaleRefund.REFUND_REFUSE_BUYER
    
    def is_confirmed(self):
        return self.status == SaleOrder.TRADE_FINISHED and \
            self.refund_status <= SaleRefund.REFUND_REFUSE_BUYER
    
    def is_canceled(self):
        return self.status > SaleOrder.TRADE_FINISHED or \
            self.refund_status > SaleRefund.REFUND_REFUSE_BUYER
    

def refresh_sale_trade_status(sender,instance,*args,**kwargs):
    """ 更新订单状态 """
    #TODO
    
post_save.connect(refresh_sale_trade_status, sender=SaleOrder)


def get_self_mama_id(unionid):
    from flashsale.xiaolumm.models import XiaoluMama
    records = XiaoluMama.objects.filter(openid=unionid, status=XiaoluMama.EFFECT, progress=XiaoluMama.PASS)
    if records.count() > 0:
        return records[0].pk
    return None


def add_to_mama_order_carry(sender, instance, created, **kwargs):
    """
    SaleOrder save triggers adding carry to OrderCarry.
    """
    
    extra = instance.sale_trade.extras_info
    customer_id = instance.sale_trade.buyer_id
    customer = Customer.objects.get(pk=customer_id)
    mama_id = get_self_mama_id(customer.unionid)
    via_app = instance.sale_trade.is_paid_via_app()
    
    if not mama_id:
        # customer itself is not a xiaolumama, then check 
        # 1) if customer is a fan of a mama and the order is paid via app; or
        # 2) if customer is coming from a mama's share link; 
        if via_app:
            # check fan's relationship
            from flashsale.xiaolumm.models_fans import XlmmFans
            
            fans_records = XlmmFans.objects.filter(fans_cusid=customer_id)    
            if fans_records.count() > 0:
                mama_id = fans_records[0].xlmm
        elif "mm_linkid" in extra:
            # This means customer is coming from mama's share link,
            # carry should be given to mama, regardless whether or
            # not customer is a fan of another mama.
            mama_id = extra["mm_linkid"]
        
    if not mama_id:
        return
    
    payment = instance.payment * 100
    
    from shopback.items.models import Product
    products = Product.objects.filter(id=instance.item_id)
    
    if products.count() <= 0:
        return
    
    from flashsale.xiaolumm.models import XiaoluMama
    
    product = products[0]
    mama = XiaoluMama.objects.get(pk=mama_id)
    carry_scheme = mama.get_Mama_Order_Rebeta_Scheme(product)
    agency_level = mama.agencylevel
    carry_amount = carry_scheme.get_scheme_rebeta(agencylevel=agency_level,payment=payment)
    

    from flashsale.xiaolumm.tasks_mama import update_ordercarry
    update_ordercarry.s(mama_id, instance, customer, carry_amount, agency_level, carry_scheme.name, via_app)()
        
post_save.connect(add_to_mama_order_carry, sender=SaleOrder, dispatch_uid='post_save_add_to_mama_order_carry')



class TradeCharge(PayBaseModel):
    
    order_no    = models.CharField(max_length=40,verbose_name=u'订单ID')
    charge      = models.CharField(max_length=28,verbose_name=u'支付编号')
    
    paid        = models.BooleanField(db_index=True,default=False,verbose_name=u'付款')
    refunded    = models.BooleanField(db_index=True,default=False,verbose_name=u'退款')
    
    channel     = models.CharField(max_length=16,blank=True,verbose_name=u'支付方式')
    amount      = models.CharField(max_length=10,blank=True,verbose_name=u'付款金额')
    currency    = models.CharField(max_length=8,blank=True,verbose_name=u'币种')
    
    transaction_no  = models.CharField(max_length=28,blank=True,verbose_name=u'事务NO')
    amount_refunded = models.CharField(max_length=16,blank=True,verbose_name=u'退款金额')
    
    failure_code    = models.CharField(max_length=16,blank=True,verbose_name=u'错误编码')
    failure_msg     = models.CharField(max_length=16,blank=True,verbose_name=u'错误信息')
    
#     out_trade_no    = models.CharField(max_length=32,db_index=True,blank=True,verbose_name=u'外部交易ID')
    
    time_paid       = models.DateTimeField(null=True,blank=True,db_index=True,verbose_name=u'付款时间')
    time_expire     = models.DateTimeField(null=True,blank=True,db_index=True,verbose_name=u'失效时间')
    
    class Meta:
        db_table = 'flashsale_trade_charge'
        unique_together = ("order_no","charge")
        verbose_name=u'特卖支付/交易'
        verbose_name_plural = u'特卖交易/支付列表'
        
    def __unicode__(self):
        return '<%s>'%(self.id)
    
from shopback.items.models import Product,ProductSku

class ShoppingCart(BaseModel):
    """ 购物车 """
    
    NORMAL = 0
    CANCEL = 1
    
    STATUS_CHOICE = ((NORMAL,u'正常'),
                     (CANCEL,u'关闭'))
    
    id    = BigIntegerAutoField(primary_key=True)
    buyer_id    = models.BigIntegerField(null=False,db_index=True,verbose_name=u'买家ID')
    buyer_nick  = models.CharField(max_length=64,blank=True,verbose_name=u'买家昵称')
    
    item_id  = models.CharField(max_length=64,blank=True,verbose_name=u'商品ID')
    title  =  models.CharField(max_length=128,blank=True,verbose_name=u'商品标题')
    price  = models.FloatField(default=0.0,verbose_name=u'单价')

    sku_id = models.CharField(max_length=20,blank=True,verbose_name=u'规格ID')
    num = models.IntegerField(null=True,default=0,verbose_name=u'商品数量')
    
    total_fee    = models.FloatField(default=0.0,verbose_name=u'总费用')

    sku_name = models.CharField(max_length=256,blank=True, verbose_name=u'规格名称')
    
    pic_path = models.CharField(max_length=512,blank=True,verbose_name=u'商品图片')
    remain_time   =  models.DateTimeField(null=True, blank=True, verbose_name=u'保留时间')

    status = models.IntegerField(choices=STATUS_CHOICE,default=NORMAL,
                              db_index=True,blank=True,verbose_name=u'订单状态') 
    
    class Meta:
        db_table = 'flashsale_shoppingcart'
        verbose_name=u'特卖/购物车'
        verbose_name_plural = u'特卖/购物车'
        
    def __unicode__(self):
        return '%s'%(self.id)
    
    @transaction.commit_on_success
    def close_cart(self,release_locknum=True):
        """ 关闭购物车 """
        try:
            ShoppingCart.objects.get(id=self.id, status=ShoppingCart.NORMAL)
        except ShoppingCart.DoesNotExist:
            return
    
        self.status = self.CANCEL
        self.save()
        if release_locknum:
            sku = get_object_or_404(ProductSku, pk=self.sku_id)
            Product.objects.releaseLockQuantity(sku,self.num)
    
    def std_sale_price(self):
        sku = ProductSku.objects.get(id=self.sku_id)
        return sku.std_sale_price
    
    def is_deposite(self):
        product = Product.objects.get(id=self.item_id)
        return product.outer_id.startswith('RMB')
    
    def is_good_enough(self):
        product_sku = ProductSku.objects.get(id=self.sku_id)
        return (product_sku.product.shelf_status == Product.UP_SHELF 
                and product_sku.real_remainnum >= self.num)
        
    def calc_discount_fee(self,xlmm=None):
        product_sku = ProductSku.objects.get(id=self.sku_id)
        return product_sku.calc_discount_fee(xlmm)
    
    
from signals_coupon import *
import logging
from shopback import signals
from django.contrib.auth.models import User as DjangoUser


def off_the_shelf_func(sender, product_list, *args, **kwargs):

    djuser, state = DjangoUser.objects.get_or_create(username='systemoa', is_active=True)
    for pro_bean in product_list:
        all_cart = ShoppingCart.objects.filter(item_id=pro_bean.id, status=ShoppingCart.NORMAL)
        for cart in all_cart:
            cart.close_cart()
            log_action(djuser.id, cart, CHANGE, u'下架后更新')
        all_trade = SaleTrade.objects.filter(sale_orders__item_id=pro_bean.id, status=SaleTrade.WAIT_BUYER_PAY)
        for trade in all_trade:
            try:
                trade.close_trade()
                log_action(djuser.id, trade, CHANGE, u'系统更新待付款状态到交易关闭')
            except Exception, exc:
                logger = logging.getLogger('django.request')
                logger.error(exc.message, exc_info=True)

signals.signal_product_downshelf.connect(off_the_shelf_func, sender=Product)

from models_coupon_new import CouponTemplate, CouponsPool, UserCoupon
from models_shops import CustomerShops, CuShopPros
