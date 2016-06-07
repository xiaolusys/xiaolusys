# -*- coding:utf-8 -*-
import uuid
import datetime
from django.db import models
from django.shortcuts import get_object_or_404
from django.db.models.signals import post_save
from django.db import transaction

from .base import PayBaseModel, BaseModel
from shopback.logistics.models import LogisticsCompany
from shopback.items.models import DIPOSITE_CODE_PREFIX
from shopback.items.models import Product, ProductSku
from flashsale.pay.models_user import Register, Customer, UserBudget, BudgetLog
from flashsale.pay.models_addr import District, UserAddress, UserAddressChange
from flashsale.pay.models_custom import Productdetail, GoodShelf, ModelProduct, ActivityEntry, BrandProduct, BrandEntry
from flashsale.pay.models_refund import SaleRefund
from flashsale.pay.models_envelope import Envelop
from flashsale.pay.models_coupon import Integral, IntegralLog
from flashsale.pay.models_coupon_new import UserCoupon, CouponsPool, CouponTemplate
from flashsale.pay.models_share import CustomShare
from flashsale.pay.models_faqs import FaqMainCategory, FaqsDetailCategory, SaleFaq
from flashsale.pay import managers
from flashsale.pay import constants as CONST

from .signals import signal_saletrade_pay_confirm, signal_saletrade_refund_post
from .options import uniqid
from core.fields import JSONCharMyField
from common.utils import update_model_fields
from shopback.users.models import User
import logging

logger = logging.getLogger(__name__)

FLASH_SELLER_ID = 'flashsale'
AGENCY_DIPOSITE_CODE = DIPOSITE_CODE_PREFIX
TIME_FOR_PAYMENT = 25 * 60


# seller = User.objects.get(uid='flashsale')

def genUUID():
    return str(uuid.uuid1(clock_seq=True))

def gen_uuid_trade_tid():
    return uniqid('%s%s' % (SaleTrade.PREFIX_NO, datetime.date.today().strftime('%y%m%d')))

def genTradeUniqueid():
    return gen_uuid_trade_tid()


class SaleTrade(BaseModel):
    """ payment (实付金额) = total_fee (商品总金额) + post_fee (邮费) - discount_fee (优惠金额) """
    PREFIX_NO = 'xd'
    WX = 'wx'
    ALIPAY = 'alipay'
    WX_PUB = 'wx_pub'
    ALIPAY_WAP = 'alipay_wap'
    UPMP_WAP = 'upmp_wap'
    WALLET = 'wallet'
    BUDGET = 'budget'
    APPLE = 'applepay_upacp'
    CHANNEL_CHOICES = (
        (BUDGET, u'小鹿钱包'),
        (WALLET, u'妈妈钱包'),
        (WX, u'微信APP'),
        (ALIPAY, u'支付宝APP'),
        (WX_PUB, u'微支付'),
        (ALIPAY_WAP, u'支付宝'),
        (UPMP_WAP, u'银联'),
        (APPLE, u'ApplePay'),
    )

    PREPAY = 0
    POSTPAY = 1
    TRADE_TYPE_CHOICES = (
        (PREPAY, u"在线支付"),
        (POSTPAY, "货到付款"),
    )

    SALE_ORDER = 0
    RESERVE_ORDER = 1
    DEPOSITE_ORDER = 2
    ORDER_TYPE_CHOICES = (
        (SALE_ORDER, u"特卖订单"),
        (RESERVE_ORDER, "预订制"),
        (DEPOSITE_ORDER, "押金订单"),
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
        (TRADE_NO_CREATE_PAY, u'订单创建'),
        (WAIT_BUYER_PAY, u'待付款'),
        (WAIT_SELLER_SEND_GOODS, u'已付款'),
        (WAIT_BUYER_CONFIRM_GOODS, u'已发货'),
        (TRADE_BUYER_SIGNED, u'确认签收'),
        (TRADE_FINISHED, u'交易成功'),
        (TRADE_CLOSED, u'退款关闭'),
        (TRADE_CLOSED_BY_SYS, u'交易关闭'),
    )

    id = models.AutoField(primary_key=True, verbose_name=u'订单ID')
    tid = models.CharField(max_length=40, unique=True,
                           default=genTradeUniqueid,
                           verbose_name=u'原单ID')
    buyer_id = models.BigIntegerField(null=False, db_index=True, verbose_name=u'买家ID')
    buyer_nick = models.CharField(max_length=64, blank=True, verbose_name=u'买家昵称')

    channel = models.CharField(max_length=16, db_index=True,
                               choices=CHANNEL_CHOICES, blank=True, verbose_name=u'付款方式')

    payment = models.FloatField(default=0.0, verbose_name=u'付款金额')
    pay_cash = models.FloatField(default=0.0, verbose_name=u'实付现金')
    post_fee = models.FloatField(default=0.0, verbose_name=u'物流费用')
    discount_fee = models.FloatField(default=0.0, verbose_name=u'优惠折扣')
    total_fee = models.FloatField(default=0.0, verbose_name=u'总费用')
    has_budget_paid = models.BooleanField(default=False, verbose_name=u'使用余额')

    buyer_message = models.TextField(max_length=1000, blank=True, verbose_name=u'买家留言')
    seller_memo = models.TextField(max_length=1000, blank=True, verbose_name=u'卖家备注')

    pay_time = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'付款日期')
    consign_time = models.DateTimeField(null=True, blank=True, verbose_name=u'发货日期')

    trade_type = models.IntegerField(choices=TRADE_TYPE_CHOICES, default=PREPAY, verbose_name=u'交易类型')
    order_type = models.IntegerField(choices=ORDER_TYPE_CHOICES, default=SALE_ORDER, verbose_name=u'订单类型')

    out_sid = models.CharField(max_length=64, blank=True, verbose_name=u'物流编号')
    logistics_company = models.ForeignKey(LogisticsCompany, null=True,
                                          blank=True, verbose_name=u'物流公司')
    receiver_name = models.CharField(max_length=25,
                                     blank=True, verbose_name=u'收货人姓名')
    receiver_state = models.CharField(max_length=16, blank=True, verbose_name=u'省')
    receiver_city = models.CharField(max_length=16, blank=True, verbose_name=u'市')
    receiver_district = models.CharField(max_length=16, blank=True, verbose_name=u'区')

    receiver_address = models.CharField(max_length=128, blank=True, verbose_name=u'详细地址')
    receiver_zip = models.CharField(max_length=10, blank=True, verbose_name=u'邮编')
    receiver_mobile = models.CharField(max_length=11, db_index=True, blank=True, verbose_name=u'手机')
    receiver_phone = models.CharField(max_length=20, blank=True, verbose_name=u'电话')
    user_address_id = models.BigIntegerField(blank=True, null=True, verbose_name=u'地址id')

    openid = models.CharField(max_length=40, blank=True, verbose_name=u'微信OpenID')
    charge = models.CharField(max_length=28, verbose_name=u'支付编号')

    extras_info = JSONCharMyField(max_length=256, blank=True, default={}, verbose_name=u'附加信息')

    status = models.IntegerField(choices=TRADE_STATUS, default=TRADE_NO_CREATE_PAY,
                                 db_index=True, blank=True, verbose_name=u'交易状态')

    #     is_part_consign  = models.BooleanField(db_index=True,default=False,verbose_name=u'分单发货')
    #     consign_parmas   = JSONCharMyField(max_length=512, blank=True, default='[]', verbose_name=u'发货信息')
    objects = models.Manager()
    normal_objects = managers.NormalSaleTradeManager()

    class Meta:
        db_table = 'flashsale_trade'
        app_label = 'pay'
        verbose_name = u'特卖/订单'
        verbose_name_plural = u'特卖/订单列表'

    def __unicode__(self):
        return '<%s,%s>' % (str(self.id), self.buyer_nick)

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
    def budget_payment(self):
        """ 余额支付（分） """
        if self.has_budget_paid:
            return round((self.payment - self.pay_cash) * 100)
        return 0

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

    @property
    def user_adress(self):
        user_addr = UserAddress.objects.filter(id=self.user_address_id).first()
        return {
            'id': self.user_address_id,
            'receiver_name':self.receiver_name,
            'receiver_state':self.receiver_state,
            'receiver_city':self.receiver_city,
            'receiver_district':self.receiver_district,
            'receiver_address':self.receiver_address,
            'receiver_mobile':self.receiver_mobile,
            'receiver_phone':self.receiver_phone,
            'default':user_addr and user_addr.default or ''
        }


    def get_cash_payment(self):
        """ 实际需支付金额 """
        if not self.has_budget_paid:
            return self.payment

        if self.pay_cash > 0:
            return self.pay_cash

        return self.payment

    def get_buyer_openid(self):
        """ 获取订单用户openid """
        if self.openid:
            return self.openid
        return self.order_buyer.openid

    @classmethod
    def mapTradeStatus(cls, index):
        from shopback.trades.models import MergeTrade
        status_list = MergeTrade.TAOBAO_TRADE_STATUS
        return status_list[index][0]

    def is_paid_via_app(self):
        """
        Roughly check whether order is paid via app, should be revised later.
        """
        return self.channel == SaleTrade.WX or self.channel == SaleTrade.ALIPAY

    def is_effect(self):
        return self.status in [SaleTrade.WAIT_SELLER_SEND_GOODS,
                               SaleTrade.WAIT_BUYER_CONFIRM_GOODS,
                               SaleTrade.TRADE_BUYER_SIGNED,
                               SaleTrade.TRADE_FINISHED,
                               ]

    def is_payable(self):
        now = datetime.datetime.now()
        return self.status == self.WAIT_BUYER_PAY and (now - self.created).seconds < TIME_FOR_PAYMENT

    def is_closed(self):
        return self.status == self.TRADE_CLOSED_BY_SYS

    def is_refunded(self):
        return self.status == self.TRADE_CLOSED

    def get_merge_trades(self):
        from shopback.trades.models import MergeTrade
        return MergeTrade.objects.filter(tid=self.tid)

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
        except Exception, exc:
            logger.error(exc.message, exc_info=True)

    def increase_lock_skunum(self):
        try:
            for order in self.normal_orders:
                product_sku = ProductSku.objects.get(id=order.sku_id)
                Product.objects.lockQuantity(product_sku, order.num)
        except Exception, exc:
            logger.error(exc.message, exc_info=True)

    def set_out_sid(self, out_sid=None, logistics_company_id=None):
        if not self.out_sid:
            if out_sid:
                self.out_sid = out_sid
                self.logistics_company_id = logistics_company_id
                self.save()
            else:
                from shopback.trades.models import PackageSkuItem
                for sale_order in self.sale_orders.all():
                    psi = PackageSkuItem.objects.filter(sale_order_id=sale_order.id, assign_status=2).exclude(
                        package_order_id=None).first()
                    if psi and psi.package_order.out_sid:
                        self.set_out_sid(psi.package_order.out_sid, psi.package_order.logistics_company_id)

    def confirm_payment(self):
        from django_statsd.clients import statsd
        statsd.incr('xiaolumm.postpay_count')
        statsd.incr('xiaolumm.postpay_amount', self.payment)
        signal_saletrade_pay_confirm.send(sender=SaleTrade, obj=self)

    def charge_confirm(self, charge_time=None):
        """ 如果付款期间，订单被订单号任务关闭则不减锁定数量 """
        trade_close = self.is_closed()
        self.status = self.WAIT_SELLER_SEND_GOODS
        self.pay_time = charge_time or datetime.datetime.now()
        update_model_fields(self, update_fields=['status', 'pay_time'])

        for order in self.sale_orders.all():
            order.status = order.WAIT_SELLER_SEND_GOODS
            order.pay_time = self.pay_time
            order.save()
        # 付款后订单被关闭，则加上锁定数
        if trade_close:
            self.increase_lock_skunum()
        # 如果使用余额支付,付款成功后则扣除
        if self.has_budget_paid:
            try:
                user_budget = UserBudget.objects.get(user_id=self.buyer_id)
                user_budget.charge_confirm(self.id)
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
        self.confirm_payment()

    def change_sku_item(self, old_sale_order, sku_id, num=1):
        """
            更换sku
        :param old_sale_order:
        :return:
        """

        if not old_sale_order.can_change_sku():
            raise Exception(u'已发货或退款的商品不能执行换货')
        sku = ProductSku.objects.get(id=sku_id)
        # from shopback.items.models import ProductSkuStats
        # sku_stock = ProductSkuStats.objects.get(sku_id=sku_id)
        # if sku_stock.realtime_quantity < num:
        #     raise Exception(u'换货数必须小于实时库存')
        old_sale_order.status = SaleOrder.TRADE_CLOSED_BY_SYS
        old_sale_order.save()
        new_sale_order = old_sale_order
        new_sale_order.id = None
        cnt = self.sale_orders.count()
        new_sale_order.oid = '%s-%s' % (old_sale_order.oid, str(cnt))
        new_sale_order.status = SaleOrder.WAIT_SELLER_SEND_GOODS
        new_sale_order.sku_id = sku_id
        product = sku.product
        new_sale_order.outer_id = product.outer_id
        new_sale_order.outer_sku_id = sku.outer_id
        new_sale_order.num = num
        new_sale_order.sku_name = sku.properties_alias
        new_sale_order.title = product.name
        new_sale_order.pic_path = product.pic_path
        new_sale_order.pay_time = datetime.datetime.now()
        new_sale_order.refund_id = None
        new_sale_order.refund_fee = 0
        new_sale_order.refund_status = SaleRefund.NO_REFUND
        new_sale_order.save()

    @transaction.atomic
    def close_trade(self):
        """ 关闭待付款订单 """
        try:
            SaleTrade.objects.get(id=self.id, status=SaleTrade.WAIT_BUYER_PAY)
        except SaleTrade.DoesNotExist:
            return
        self.status = SaleTrade.TRADE_CLOSED_BY_SYS
        self.save()

        for order in self.normal_orders:
            order.close_order()

        if self.has_budget_paid:
            ubudget = UserBudget.objects.get(user=self.buyer_id)
            ubudget.charge_cancel(self.id)
        # 释放被当前订单使用的优惠券
        self.release_coupon()

    def release_coupon(self):
        """ 释放订单对应的优惠券 """
        from flashsale.coupon.models import UserCoupon
        coupon_id = self.extras_info.get("coupon") or None
        usercoupon = UserCoupon.objects.filter(id=coupon_id).first()
        if usercoupon is None:
            return 
        usercoupon.release_usercoupon()  # 修改该优惠券的状态到未使用

    @property
    def unsign_orders(self):
        """ 允许签收的订单 （已经付款、已发货、货到付款签收）"""
        return self.sale_orders.filter(status__in=
                                       (SaleOrder.WAIT_SELLER_SEND_GOODS,
                                        SaleOrder.WAIT_BUYER_CONFIRM_GOODS,
                                        SaleOrder.TRADE_BUYER_SIGNED))

    @property
    def seller(self):
        if not hasattr(SaleTrade, '_seller'):
            SaleTrade._seller = User.objects.get(uid=FLASH_SELLER_ID)
        return SaleTrade._seller

    def confirm_sign_trade(self):
        """确认签收 修改该交易 状态到交易完成 """
        SaleTrade.objects.get(id=self.id)
        for order in self.unsign_orders:
            order.confirm_sign_order()  # 同时修改正常订单到交易完成
        self.status = SaleTrade.TRADE_FINISHED
        self.save()

    def get_logistics_by_orders(self):
        """ 获取订单所属仓库 """
        ware_by = None
        product_ids = self.sale_orders.values_list('item_id',flat=True)
        for product_id in product_ids:
            product = Product.objects.filter(id=product_id).first()
            if product and ware_by is None:
                ware_by = product.ware_by
                continue
            if product:
                ware_by &= product.ware_by
        return ware_by or Product.WARE_NONE


def record_supplier_args(sender, obj, **kwargs):
    """ 随支付成功信号 更新供应商的销售额，销售数量
        :arg obj -> SaleTrade instance
        :except None
        :return None
    """
    try:
        normal_orders = obj.normal_orders.all()
        for order in normal_orders:
            item_id = order.item_id
            pro = Product.objects.get(id=item_id)
            sal_p, supplier = pro.pro_sale_supplier()
            if supplier is not None:
                supplier.total_sale_num = F('total_sale_num') + order.num
                supplier.total_sale_amount = F("total_sale_amount") + order.payment
                update_model_fields(supplier, update_fields=['total_sale_num', 'total_sale_amount'])
    except Exception, exc:
        logger.error('record_supplier_args error:%s' % exc.message, exc_info=True)


signal_saletrade_pay_confirm.connect(record_supplier_args, sender=SaleTrade)

from shopback.categorys.models import CategorySaleStat


def category_trade_stat(sender, obj, **kwargs):
    """记录不同类别产品的销售数量和销售金额"""
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
        except Exception, exc:
            logger.error(exc.message, exc_info=True)


signal_saletrade_pay_confirm.connect(category_trade_stat, sender=SaleTrade)

def push_msg_mama(sender, obj, **kwargs):
    """专属链接有人下单后则推送消息给代理"""
    from flashsale.xiaolumm.tasks_mama_push import task_push_mama_order_msg
    task_push_mama_order_msg.s(obj).delay()


def trade_payment_used_coupon(sender, obj, **kwargs):
    """ 交易支付后修改优惠券状态为使用 """
    from flashsale.coupon.tasks import task_change_coupon_status_used
    task_change_coupon_status_used(obj)  # execute immediately not delay


def release_mamalink_coupon(sender, obj, **kwargs):
    """用户下单成功后给专属链接代理 发放优惠券"""
    from flashsale.coupon.tasks import task_release_mama_link_coupon
    task_release_mama_link_coupon.delay(obj)


def release_coupon_buy_way(sender, obj, **kwargs):
    """购买成功触发购买成功发放的优惠券"""
    from flashsale.coupon.tasks import task_release_coupon_for_order
    task_release_coupon_for_order.delay(obj)


def freeze_coupon_by_refund(sender, obj, **kwargs):
    """用户退款冻结绑定的优惠券"""
    from flashsale.coupon.tasks import task_freeze_coupon_by_refund
    task_freeze_coupon_by_refund.delay(obj)

signal_saletrade_pay_confirm.connect(push_msg_mama, sender=SaleTrade)
signal_saletrade_pay_confirm.connect(trade_payment_used_coupon, sender=SaleTrade)
signal_saletrade_pay_confirm.connect(release_coupon_buy_way, sender=SaleTrade)
signal_saletrade_pay_confirm.connect(release_mamalink_coupon, sender=SaleTrade)
signal_saletrade_refund_post.connect(freeze_coupon_by_refund, sender=SaleRefund)


def default_oid():
    return uniqid('%s%s' % (SaleOrder.PREFIX_NO, datetime.date.today().strftime('%y%m%d')))


def default_extras():
    return {}


class SaleOrder(PayBaseModel):
    """ 特卖订单明细 """

    class Meta:
        db_table = 'flashsale_order'
        app_label = 'pay'
        verbose_name = u'特卖/订单明细'
        verbose_name_plural = u'特卖/订单明细列表'

    PREFIX_NO = 'xo'
    TRADE_NO_CREATE_PAY = 0
    WAIT_BUYER_PAY = 1
    WAIT_SELLER_SEND_GOODS = 2
    WAIT_BUYER_CONFIRM_GOODS = 3
    TRADE_BUYER_SIGNED = 4
    TRADE_FINISHED = 5
    TRADE_CLOSED = 6
    TRADE_CLOSED_BY_SYS = 7
    ORDER_STATUS = (
        (TRADE_NO_CREATE_PAY, u'订单创建'),
        (WAIT_BUYER_PAY, u'待付款'),
        (WAIT_SELLER_SEND_GOODS, u'已付款'),
        (WAIT_BUYER_CONFIRM_GOODS, u'已发货'),
        (TRADE_BUYER_SIGNED, u'确认签收'),
        (TRADE_FINISHED, u'交易成功'),
        (TRADE_CLOSED, u'退款关闭'),
        (TRADE_CLOSED_BY_SYS, u'交易关闭'),
    )

    NORMAL_ORDER_STATUS = (WAIT_BUYER_PAY,
                           WAIT_SELLER_SEND_GOODS,
                           WAIT_BUYER_CONFIRM_GOODS,
                           TRADE_BUYER_SIGNED,
                           TRADE_FINISHED,)

    id = models.AutoField(primary_key=True)
    oid = models.CharField(max_length=40, unique=True,
                           default=default_oid,
                           verbose_name=u'原单ID')
    sale_trade = models.ForeignKey(SaleTrade, related_name='sale_orders',
                                   verbose_name=u'所属订单')

    buyer_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'买家ID')

    item_id = models.CharField(max_length=64, blank=True, verbose_name=u'商品ID')
    title = models.CharField(max_length=128, blank=True, verbose_name=u'商品标题')
    price = models.FloatField(default=0.0, verbose_name=u'商品单价')

    sku_id = models.CharField(max_length=20, blank=True, verbose_name=u'属性编码')
    num = models.IntegerField(null=True, default=0, verbose_name=u'商品数量')

    outer_id = models.CharField(max_length=32, blank=True, verbose_name=u'商品外部编码')
    outer_sku_id = models.CharField(max_length=32, blank=True, verbose_name=u'规格外部编码')

    total_fee = models.FloatField(default=0.0, verbose_name=u'总费用')
    payment = models.FloatField(default=0.0, verbose_name=u'实付款')
    discount_fee = models.FloatField(default=0.0, verbose_name=u'优惠金额')

    sku_name = models.CharField(max_length=256, blank=True,
                                verbose_name=u'购买规格')
    pic_path = models.CharField(max_length=512, blank=True, verbose_name=u'商品图片')

    pay_time = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'付款日期')
    consign_time = models.DateTimeField(null=True, blank=True, verbose_name=u'发货日期')
    sign_time = models.DateTimeField(null=True, blank=True, verbose_name=u'签收日期')

    refund_id = models.BigIntegerField(null=True, verbose_name=u'退款ID')
    refund_fee = models.FloatField(default=0.0, verbose_name=u'退款费用')
    refund_status = models.IntegerField(choices=SaleRefund.REFUND_STATUS,
                                        default=SaleRefund.NO_REFUND,
                                        blank=True, verbose_name='退款状态')

    status = models.IntegerField(choices=ORDER_STATUS, default=TRADE_NO_CREATE_PAY,
                                 db_index=True, blank=True, verbose_name=u'订单状态')
    extras = JSONCharMyField(blank=True, default=default_extras, verbose_name=u'附加信息')

    def __unicode__(self):
        return '<%s>' % (self.id)

    def can_change_sku(self):
        if self.status != SaleOrder.WAIT_SELLER_SEND_GOODS\
            or self.refund_status in [SaleRefund.REFUND_WAIT_RETURN_GOODS,
                                                SaleRefund.REFUND_CONFIRM_GOODS,
                                                SaleRefund.REFUND_APPROVE,
                                                SaleRefund.REFUND_SUCCESS]:
            return False
        else:
            return True

    def save(self, *args, **kwargs):
        # if saleorder not set buyer_id, set saletrade buyer_id to it
        if not self.buyer_id:
            self.buyer_id = self.sale_trade.buyer_id
        return super(SaleOrder, self).save(*args, **kwargs)

    @property
    def refund(self):
        try:
            refund = SaleRefund.objects.get(trade_id=self.sale_trade.id, order_id=self.id)
            return refund
        except:
            return None

    @property
    def package_order(self):
        if not self.package_order_id:
            return None
        try:
            from shopback.trades.models import PackageOrder
            return PackageOrder.objects.get(id=self.package_order_id)
        except:
            return None

    @property
    def refundable(self):
        return self.sale_trade.status in SaleTrade.REFUNDABLE_STATUS

    def do_refund(self):
        pass

    def is_finishable(self):
        """
        1，订单发货后超过14天未确认签收,系统自动变成已完成状态；
        2，订单确认签收后，7天之后(最多7天,应在在发货后14天以内)订单状态变成已完成；
        """
        now_time = datetime.datetime.now()
        consign_time = self.consign_time
        sign_time = self.sign_time
        if self.refund_status in SaleRefund.REFUNDABLE_STATUS:
            return False
        delta_days = consign_time and (now_time - consign_time).days or 0
        if (self.status == self.WAIT_BUYER_CONFIRM_GOODS
            and (delta_days > CONST.ORDER_WAIT_CONFIRM_TO_FINISHED_DAYS)):
            return True
        elif (self.status == self.TRADE_BUYER_SIGNED
              and (not sign_time
                   or (now_time - sign_time).days > CONST.ORDER_SIGNED_TO_FINISHED_DAYS
                   or delta_days > CONST.ORDER_WAIT_CONFIRM_TO_FINISHED_DAYS)):
            return True
        return False

    def close_order(self):
        """ 待付款关闭订单 """
        try:
            SaleOrder.objects.get(id=self.id, status=SaleOrder.WAIT_BUYER_PAY)
        except SaleOrder.DoesNotExist, exc:
            return

        self.status = self.TRADE_CLOSED_BY_SYS
        self.save()
        sku = get_object_or_404(ProductSku, pk=self.sku_id)
        Product.objects.releaseLockQuantity(sku, self.num)

    def confirm_sign_order(self):
        """确认签收 修改该订单状态到 确认签收状态"""
        self.status = self.TRADE_BUYER_SIGNED
        self.sign_time = datetime.datetime.now()
        self.save()

        sale_trade = self.sale_trade
        normal_orders = sale_trade.normal_orders
        sign_orders = sale_trade.sale_orders.filter(status=SaleOrder.TRADE_BUYER_SIGNED)
        if sign_orders.count() == normal_orders.count():
            sale_trade.status = SaleTrade.TRADE_BUYER_SIGNED
            update_model_fields(sale_trade, update_fields=['status'])

    # def cancel_assign(self):
    #     if self.assign_status == SaleOrder.ASSIGNED:
    #         self.assign_status = SaleOrder.NOT_ASSIGNED
    #         self.package_order_id = None
    #         self.save()
    #         psku = ProductSku.objects.get(id=self.sku_id)
    #         psku.assign_num -= self.num
    #         psku.save()
    #         return True
    #     return False

    def is_seckill(self):
        return True if self.title.startswith(u'秒杀') else False

    def second_kill_title(self):
        """ 判断是否秒杀标题　"""
        return self.is_seckill()

    def is_pending(self):
        return self.status == SaleOrder.WAIT_SELLER_SEND_GOODS and \
               self.refund_status <= SaleRefund.REFUND_REFUSE_BUYER

    def is_confirmed(self):
        return self.status >= SaleOrder.WAIT_BUYER_CONFIRM_GOODS and \
               self.status <= SaleOrder.TRADE_FINISHED and \
               self.refund_status <= SaleRefund.REFUND_REFUSE_BUYER

    def is_canceled(self):
        return self.status > SaleOrder.TRADE_FINISHED or \
               self.refund_status > SaleRefund.REFUND_REFUSE_BUYER

    def is_deposit(self):
        return self.outer_id.startswith('RMB')

    def stats_not_pay(self):
        return self.status == SaleOrder.TRADE_NO_CREATE_PAY or \
               self.status == SaleOrder.WAIT_BUYER_PAY or self.status == SaleOrder.TRADE_CLOSED_BY_SYS

    def stats_paid(self):
        """ 统计付款的 """
        return SaleOrder.WAIT_SELLER_SEND_GOODS <= self.status \
               <= SaleOrder.TRADE_FINISHED and self.refund_status <= SaleRefund.REFUND_REFUSE_BUYER

    def stats_cancel(self):
        """ 发货前退单 """
        refund = SaleRefund.objects.filter(id=self.refund_id).first()
        if refund and refund.good_status == SaleRefund.BUYER_NOT_RECEIVED:  # 买家没有收到货(卖家没有发货 == 发货前)
            return self.status not in [  # 不在以下状态认为是 有 付过款
                                         SaleOrder.TRADE_NO_CREATE_PAY,  # 创建
                                         SaleOrder.WAIT_BUYER_PAY,  # 待付款
                                         SaleOrder.TRADE_CLOSED_BY_SYS  # 交易关闭
                                         ] and self.refund_status not in [  # 不在以下状态 认为在退款状态
                                                                            SaleRefund.REFUND_CLOSED,  # 退款单关闭掉
                                                                            SaleRefund.NO_REFUND,  # 没有退款
                                                                            SaleRefund.REFUND_REFUSE_BUYER]  # 拒绝退款
        return False

    def stats_out_stock(self):
        """ 缺货退款 """
        refund = SaleRefund.objects.filter(id=self.refund_id).first()
        if refund and refund.good_status == SaleRefund.SELLER_OUT_STOCK:  # 退款单 为  缺货退款单
            return self.status not in [  # 不在以下状态认为是 有 付过款
                                         SaleOrder.TRADE_NO_CREATE_PAY,  # 创建
                                         SaleOrder.WAIT_BUYER_PAY,  # 待付款
                                         SaleOrder.TRADE_CLOSED_BY_SYS  # 交易关闭
                                         ] and self.refund_status not in [  # 不在以下状态 认为在退款状态
                                                                            SaleRefund.REFUND_CLOSED,  # 退款单关闭掉
                                                                            SaleRefund.NO_REFUND,  # 没有退款
                                                                            SaleRefund.REFUND_REFUSE_BUYER]  # 拒绝退款
        return False

    def stats_return_goods(self):
        """ 退货退款 """
        refund = SaleRefund.objects.filter(id=self.refund_id).first()
        if refund and refund.good_status in [SaleRefund.BUYER_RECEIVED,
                                             SaleRefund.BUYER_RETURNED_GOODS]:  # (买家收到货/卖家已经退货 == 发货后)
            return self.status not in [  # 不在以下状态认为是 有 付过款
                                         SaleOrder.TRADE_NO_CREATE_PAY,  # 创建
                                         SaleOrder.WAIT_BUYER_PAY,  # 待付款
                                         SaleOrder.TRADE_CLOSED_BY_SYS  # 交易关闭
                                         ] and self.refund_status not in [  # 不在以下状态 认为在退款状态
                                                                            SaleRefund.REFUND_CLOSED,  # 退款单关闭掉
                                                                            SaleRefund.NO_REFUND,  # 没有退款
                                                                            SaleRefund.REFUND_REFUSE_BUYER]  # 拒绝退款
        return False


def order_trigger(sender, instance, created, **kwargs):
    """
    SaleOrder save triggers adding carry to OrderCarry.
    """
    if instance.is_deposit():
        if instance.is_confirmed():
            from flashsale.xiaolumm.tasks_mama_relationship_visitor import task_update_referal_relationship
            task_update_referal_relationship.delay(instance)
    else:
        from flashsale.xiaolumm import tasks_mama
        tasks_mama.task_order_trigger.delay(instance)


post_save.connect(order_trigger, sender=SaleOrder, dispatch_uid='post_save_order_trigger')


def update_package_sku_item(sender, instance, created, **kwargs):
    """ 更新PackageSkuItem状态 """
    if instance.status >= SaleOrder.WAIT_SELLER_SEND_GOODS and not instance.is_deposit():
        from flashsale.pay.tasks import task_saleorder_update_package_sku_item
        task_saleorder_update_package_sku_item.delay(instance)


post_save.connect(update_package_sku_item, sender=SaleOrder, dispatch_uid='post_save_update_package_sku_item')


def saleorder_update_productskustats_waitingpay_num(sender, instance, *args, **kwargs):
    from flashsale.pay.tasks_stats import task_saleorder_update_productskustats_waitingpay_num
    task_saleorder_update_productskustats_waitingpay_num.delay(instance.sku_id)


post_save.connect(saleorder_update_productskustats_waitingpay_num, sender=SaleOrder,
                  dispatch_uid='post_save_aleorder_update_productskustats_waitingpay_num')


def saleorder_update_saletrade_status(sender, instance, *args, **kwargs):
    if instance.status == SaleOrder.WAIT_BUYER_CONFIRM_GOODS and \
                    instance.sale_trade.status < SaleTrade.WAIT_BUYER_CONFIRM_GOODS:
        from flashsale.pay.tasks import tasks_update_sale_trade_status
        tasks_update_sale_trade_status.delay(instance.sale_trade_id)


post_save.connect(saleorder_update_saletrade_status, sender=SaleOrder,
                  dispatch_uid='post_save_saleorder_update_saletrade_status')


def saleorder_update_stats_record(sender, instance, *args, **kwargs):
    from statistics.tasks import task_update_sale_order_stats_record
    task_update_sale_order_stats_record.delay(instance)

post_save.connect(saleorder_update_stats_record, sender=SaleOrder,
                  dispatch_uid='post_save_saleorder_update_stats_record')


class TradeCharge(PayBaseModel):
    order_no = models.CharField(max_length=40, verbose_name=u'订单ID')
    charge = models.CharField(max_length=28, verbose_name=u'支付编号')

    paid = models.BooleanField(db_index=True, default=False, verbose_name=u'付款')
    refunded = models.BooleanField(db_index=True, default=False, verbose_name=u'退款')

    channel = models.CharField(max_length=16, blank=True, verbose_name=u'支付方式')
    amount = models.CharField(max_length=10, blank=True, verbose_name=u'付款金额')
    currency = models.CharField(max_length=8, blank=True, verbose_name=u'币种')

    transaction_no = models.CharField(max_length=28, blank=True, verbose_name=u'事务NO')
    amount_refunded = models.CharField(max_length=16, blank=True, verbose_name=u'退款金额')

    failure_code = models.CharField(max_length=16, blank=True, verbose_name=u'错误编码')
    failure_msg = models.CharField(max_length=16, blank=True, verbose_name=u'错误信息')

    #     out_trade_no    = models.CharField(max_length=32,db_index=True,blank=True,verbose_name=u'外部交易ID')

    time_paid = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=u'付款时间')
    time_expire = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=u'失效时间')

    class Meta:
        db_table = 'flashsale_trade_charge'
        unique_together = ("order_no", "charge")
        app_label = 'pay'
        verbose_name = u'特卖支付/交易'
        verbose_name_plural = u'特卖交易/支付列表'

    def __unicode__(self):
        return '<%s>' % (self.id)


class ShoppingCart(BaseModel):
    """ 购物车 """

    NORMAL = 0
    CANCEL = 1

    STATUS_CHOICE = ((NORMAL, u'正常'),
                     (CANCEL, u'关闭'))

    id = models.AutoField(primary_key=True)
    buyer_id = models.BigIntegerField(null=False, db_index=True, verbose_name=u'买家ID')
    buyer_nick = models.CharField(max_length=64, blank=True, verbose_name=u'买家昵称')

    item_id = models.CharField(max_length=64, blank=True, verbose_name=u'商品ID')
    title = models.CharField(max_length=128, blank=True, verbose_name=u'商品标题')
    price = models.FloatField(default=0.0, verbose_name=u'单价')
    std_sale_price = models.FloatField(default=0.0, verbose_name=u'标准售价')

    sku_id = models.CharField(max_length=20, blank=True, verbose_name=u'规格ID')
    num = models.IntegerField(null=True, default=0, verbose_name=u'商品数量')

    total_fee = models.FloatField(default=0.0, verbose_name=u'总费用')

    sku_name = models.CharField(max_length=256, blank=True, verbose_name=u'规格名称')

    pic_path = models.CharField(max_length=512, blank=True, verbose_name=u'商品图片')
    remain_time = models.DateTimeField(null=True, blank=True, verbose_name=u'保留时间')

    status = models.IntegerField(choices=STATUS_CHOICE, default=NORMAL,
                                 db_index=True, blank=True, verbose_name=u'订单状态')

    class Meta:
        db_table = 'flashsale_shoppingcart'
        index_together = [('buyer_id', 'item_id', 'sku_id')]
        app_label = 'pay'
        verbose_name = u'特卖/购物车'
        verbose_name_plural = u'特卖/购物车'

    def __unicode__(self):
        return '%s' % (self.id)

    @transaction.atomic
    def close_cart(self, release_locknum=True):
        """ 关闭购物车 """
        try:
            ShoppingCart.objects.get(id=self.id, status=ShoppingCart.NORMAL)
        except ShoppingCart.DoesNotExist:
            return

        self.status = self.CANCEL
        self.save()
        if release_locknum:
            sku = get_object_or_404(ProductSku, pk=self.sku_id)
            Product.objects.releaseLockQuantity(sku, self.num)

    # def std_sale_price(self):
    #     sku = ProductSku.objects.get(id=self.sku_id)
    #     return sku.std_sale_price

    def is_deposite(self):
        product = Product.objects.get(id=self.item_id)
        return product.outer_id.startswith('RMB')

    def is_good_enough(self):
        product_sku = ProductSku.objects.get(id=self.sku_id)
        return (product_sku.product.shelf_status == Product.UP_SHELF
                and product_sku.real_remainnum >= self.num)

    def calc_discount_fee(self, xlmm=None):
        product_sku = ProductSku.objects.get(id=self.sku_id)
        return product_sku.calc_discount_fee(xlmm)

    def is_repayable(self):
        """ can repay able """
        pro_sku = ProductSku.objects.filter(id=self.sku_id).first()
        if pro_sku and pro_sku.product.is_onshelf():
            return pro_sku.sale_out
        return False


from signals_coupon import *
from shopback import signals
from django.contrib.auth.models import User as DjangoUser


def off_the_shelf_func(sender, product_list, *args, **kwargs):
    from core.options import log_action, CHANGE, get_systemoa_user
    sysoa_user = get_systemoa_user()
    for pro_bean in product_list:
        all_cart = ShoppingCart.objects.filter(item_id=pro_bean.id, status=ShoppingCart.NORMAL)
        for cart in all_cart:
            cart.close_cart()
            log_action(sysoa_user.id, cart, CHANGE, u'下架后更新')
        all_trade = SaleTrade.objects.filter(sale_orders__item_id=pro_bean.id, status=SaleTrade.WAIT_BUYER_PAY)
        for trade in all_trade:
            try:
                trade.close_trade()
                log_action(sysoa_user.id, trade, CHANGE, u'系统更新待付款状态到交易关闭')
            except Exception, exc:
                logger.error(exc.message, exc_info=True)


signals.signal_product_downshelf.connect(off_the_shelf_func, sender=Product)


def shoppingcart_update_productskustats_shoppingcart_num(sender, instance, *args, **kwargs):
    from flashsale.pay.tasks_stats import task_shoppingcart_update_productskustats_shoppingcart_num
    task_shoppingcart_update_productskustats_shoppingcart_num.delay(instance.sku_id)


post_save.connect(shoppingcart_update_productskustats_shoppingcart_num, sender=ShoppingCart,
                  dispatch_uid='post_save_shoppingcart_update_productskustats_shoppingcart_num')

from models_coupon_new import CouponTemplate, CouponsPool, UserCoupon
from models_shops import CustomerShops, CuShopPros


def check_SaleRefund_Status(sender, instance, created, **kwargs):
    # created 表示实例是否创建 （修改）
    # 允许抛出异常
    order = SaleOrder.objects.get(id=instance.order_id)
    trade = SaleTrade.objects.get(id=instance.trade_id)
    # 退款成功  如果是退款关闭要不要考虑？？？
    if instance.status == SaleRefund.REFUND_SUCCESS:
        # 如果是退款成功状态
        # 找到订单
        refund_num = instance.refund_num  # 退款数量
        order_num = order.num  # 订单数量
        if refund_num == order_num:  # 退款数量等于订单数量
            # 关闭这个订单
            order.status = SaleOrder.TRADE_CLOSED  # 退款关闭
            order.save()
        """ 判断交易状态 """
        orders = trade.sale_orders.all()
        flag_re = 0
        for orde in orders:
            if orde.status == SaleOrder.TRADE_CLOSED:
                flag_re += 1

        if flag_re == orders.count():  # 所有订单都退款成功
            # 这笔交易 退款 关闭
            trade.status = SaleTrade.TRADE_CLOSED
            trade.save()

    if instance.status == SaleRefund.REFUND_CLOSED:  # 退款关闭即没有退款成功 切换订单到交易成功状态
        # 如果是退款成功状态 找到订单
        refund_num = instance.refund_num  # 退款数量
        order_num = order.num  # 订单数量
        if refund_num == order_num:  # 退款数量等于订单数量
            order.status = SaleOrder.TRADE_FINISHED  # 交易成功
            order.save()
        """ 判断交易状态 """
        orders = trade.sale_orders.all()
        flag_re = 0
        for orde in orders:
            if orde.status == SaleOrder.TRADE_FINISHED:
                flag_re += 1

        if flag_re == orders.count():  # 所有订单都退款关闭
            # 这笔交易　交易成功
            trade.status = SaleTrade.TRADE_FINISHED
            trade.save()

    """ 同步退款状态到订单，这里至更新 退款的状态到订单的 退款状态字段 """
    order.refund_status = instance.status
    order.save()  # 保存同步的状态


post_save.connect(check_SaleRefund_Status, sender=SaleRefund)
