# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import uuid
import datetime
import urlparse
import traceback
from django.db import models
from django.conf import settings
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.db.models.signals import post_save, pre_save
from django.db import transaction
from django.dispatch import receiver

from .base import PayBaseModel, BaseModel
from shopback.logistics.models import LogisticsCompany
from shopback.items.models import Product
from .product import ProductSku
from shopback.users.models import User
from flashsale.pay import constants as CONST

from ..signals import signal_saletrade_pay_confirm, signal_saleorder_post_update
from core.utils.unikey import uniqid
from core.fields import JSONCharMyField
from core.utils.modelutils import update_model_fields

from shopback.warehouse import WARE_NONE, WARE_GZ, WARE_SH, WARE_CHOICES, WARE_THIRD
from .address import UserAddress
from .refund import SaleRefund
from .user import Customer, UserBudget
from ..managers import saletrade
import logging

logger = logging.getLogger(__name__)

FLASH_SELLER_ID  = 'flashsale'
AGENCY_DIPOSITE_CODE = Product.DIPOSITE_CODE_PREFIX
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
    WEAPP = 'weapp'
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
        (WEAPP, u'小程序支付'),
        (ALIPAY, u'支付宝APP'),
        (WX_PUB, u'微信WAP'),
        (ALIPAY_WAP, u'支付宝WAP'),
        (UPMP_WAP, u'银联'),
        (APPLE, u'ApplePay'),
    )

    PREPAY = 0
    POSTPAY = 1
    TRADE_TYPE_CHOICES = (
        (PREPAY, u"在线支付"),
        (POSTPAY, u"货到付款"),
    )

    SALE_ORDER = 0
    RESERVE_ORDER = 1
    DEPOSITE_ORDER = 2
    TEAMBUY_ORDER = 3
    ELECTRONIC_GOODS_ORDER = 4
    ORDER_TYPE_CHOICES = (
        (SALE_ORDER, u"特卖订单"),
        (RESERVE_ORDER, u"预订制"),
        (TEAMBUY_ORDER, u"团购订单"),
        (DEPOSITE_ORDER, u"押金订单"),
        (ELECTRONIC_GOODS_ORDER, u"电子商品订单"),
    )

    TRADE_NO_CREATE_PAY = 0
    WAIT_BUYER_PAY = 1
    WAIT_SELLER_SEND_GOODS = 2
    WAIT_BUYER_CONFIRM_GOODS = 3
    TRADE_BUYER_SIGNED = 4
    TRADE_FINISHED = 5
    TRADE_CLOSED = 6
    TRADE_CLOSED_BY_SYS = 7
    NORMAL_TRADE_STATUS = (
        WAIT_BUYER_PAY,
        WAIT_SELLER_SEND_GOODS,
        WAIT_BUYER_CONFIRM_GOODS,
        TRADE_BUYER_SIGNED,
        TRADE_FINISHED,
        TRADE_CLOSED,
        TRADE_CLOSED_BY_SYS
    )

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

    total_fee = models.FloatField(default=0.0, verbose_name=u'总费用')
    payment = models.FloatField(default=0.0, verbose_name=u'付款金额')
    pay_cash = models.FloatField(default=0.0, verbose_name=u'实付现金')
    post_fee = models.FloatField(default=0.0, verbose_name=u'物流费用')
    discount_fee = models.FloatField(default=0.0, verbose_name=u'优惠折扣')
    budget_paid = models.FloatField(default=0.0, verbose_name=u'余额支付')
    coin_paid   = models.FloatField(default=0.0, verbose_name=u'小鹿币支付')

    has_budget_paid = models.BooleanField(default=False, verbose_name=u'使用余额')
    has_coin_paid   = models.BooleanField(default=False, verbose_name=u'使用小鹿币')
    is_boutique     = models.BooleanField(default=False, db_index=True, verbose_name=u'精品订单')

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
    normal_objects = saletrade.NormalSaleTradeManager()

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
            return int(round(self.budget_paid * 100))
        return 0

    @property
    def coin_payment(self):
        """ 余额支付（分） """
        if self.has_coin_paid:
            return int(round(self.coin_paid * 100))
        return 0

    @property
    def status_name(self):
        if self.status in (SaleTrade.WAIT_SELLER_SEND_GOODS, SaleTrade.TRADE_BUYER_SIGNED):
            is_complete_refunding = True
            for sorder in self.sale_orders.all():
                if sorder.refund_status < CONST.REFUND_WAIT_SELLER_AGREE:
                    is_complete_refunding = False
            if is_complete_refunding and self.status == SaleTrade.WAIT_SELLER_SEND_GOODS:
                return u'退款中'
            elif is_complete_refunding and self.status == SaleTrade.TRADE_BUYER_SIGNED:
                return u'退货中'
        return self.get_status_display()

    @property
    def body_describe(self):
        subc = ''
        for order in self.sale_orders.all():
            subc += order.title
        return subc

    @property
    def receiver_address_detail(self):
        return str(self.receiver_state) + str(self.receiver_city) + str(self.receiver_district) + str(
            self.receiver_address)

    @property
    def order_buyer(self):
        return Customer.objects.get(id=self.buyer_id)

    @property
    def user_adress(self):
        user_addr = UserAddress.objects.filter(id=self.user_address_id).first()
        return {
            'id': self.user_address_id,
            'receiver_name': self.receiver_name,
            'receiver_state': self.receiver_state,
            'receiver_city': self.receiver_city,
            'receiver_district': self.receiver_district,
            'receiver_address': self.receiver_address,
            'receiver_mobile': self.receiver_mobile,
            'receiver_phone': self.receiver_phone,
            'default': user_addr and user_addr.default or '',
            'identification_no': user_addr and user_addr.identification_no or ''
        }

    def can_refund(self):
        return self.order_type == 0 and self.status in [SaleTrade.WAIT_SELLER_SEND_GOODS]

    def can_change_address(self):
        """
            如果包含第三方发货的包裹，一订货就不容许换地址了
        """
        if self.status in [SaleTrade.WAIT_SELLER_SEND_GOODS]:
            if self.order_type in [SaleTrade.TEAMBUY_ORDER, SaleTrade.SALE_ORDER]:
                for so in self.sale_orders.all():
                    if so.product.ware_by == WARE_THIRD and so.package_sku and so.package_sku.is_booked():
                        return False
            return True
        return False

    def get_cash_payment(self):
        """ 实际需支付现金 """
        return round(self.pay_cash * 100)

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

    @property
    def is_paid(self):
        return self.pay_time is not None and \
               self.status not in (SaleTrade.TRADE_CLOSED,
                                   SaleTrade.TRADE_NO_CREATE_PAY,
                                   SaleTrade.WAIT_BUYER_PAY)

    def is_paid_via_app(self):
        """
        Roughly check whether order is paid via app, should be revised later.
        """
        return self.channel == SaleTrade.WX or self.channel == SaleTrade.ALIPAY or self.channel == SaleTrade.BUDGET

    def is_effect(self):
        return self.status in [SaleTrade.WAIT_SELLER_SEND_GOODS,
                               SaleTrade.WAIT_BUYER_CONFIRM_GOODS,
                               SaleTrade.TRADE_BUYER_SIGNED,
                               SaleTrade.TRADE_FINISHED,
                               ]

    def is_payable(self):
        now = datetime.datetime.now()
        return self.status == self.WAIT_BUYER_PAY and abs(now - self.created).seconds < TIME_FOR_PAYMENT

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

    def is_budget_paid(self):
        return self.channel == SaleTrade.BUDGET or self.has_budget_paid

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
        try:
            from django_statsd.clients import statsd
            dt_str = self.pay_time.strftime('%Y.%m.%d')
            statsd.incr('xiaolumm.postpay_count.%s' % dt_str)
            statsd.incr('xiaolumm.postpay_amount.%s' % dt_str, self.payment)
            logger.info({
                'action': 'trade_confirm_signal_start',
                'order_no': self.tid,
                'action_time': datetime.datetime.now()
            })

            strade = self
            resp = signal_saletrade_pay_confirm.send_robust(sender=SaleTrade, obj=strade)
            logger.info({
                'action': 'trade_confirm_signal_end',
                'order_no': self.tid,
                'action_time': datetime.datetime.now(),
                'signal_data': '%s' % resp,
            })
        except Exception, exc:
            logger.error(str(exc), exc_info=True)
            if not settings.INGORE_SIGNAL_EXCEPTION:
                raise exc

    def charge_confirm(self, charge_time=None, charge=charge):
        """ 如果付款期间，订单被订单号任务关闭则不减锁定数量 """
        logger.info({
            'action': 'trade_confirm_start',
            'order_no': self.tid,
            'charge': charge,
            'pay_time': charge_time,
            'status': self.get_status_display(),
            'action_time': datetime.datetime.now()
        })
        try:
            with transaction.atomic():
                st = SaleTrade.objects.select_for_update().get(id=self.id)
                if st.status != SaleTrade.WAIT_BUYER_PAY:
                    logger.info({
                        'action': 'trade_confirm_exit',
                        'order_no': self.tid,
                        'status': self.get_status_display(),
                        'action_time': datetime.datetime.now()
                    })
                    return

                st.status = SaleTrade.WAIT_SELLER_SEND_GOODS
                if charge:
                    st.charge = charge
                st.pay_time = charge_time or datetime.datetime.now()
                st.save(update_fields=['status', 'pay_time', 'charge'])

                for order in st.sale_orders.all():
                    order.set_status_paid(st.pay_time)
                # 付款后订单被关闭，则加上锁定数
                # if trade_close:
                #     st.increase_lock_skunum()

                # 如果使用余额支付,付款成功后则扣除
                if st.has_budget_paid:
                    user_budget = UserBudget.objects.get(user_id=st.buyer_id)
                    user_budget.charge_confirm(st.id)

                logger.info({
                    'action': 'trade_confirm_save',
                    'order_no': self.tid,
                    'status': self.get_status_display(),
                    'action_time': datetime.datetime.now()
                })

            logger.info({
                'action': 'trade_confirm_commit',
                'order_no': self.tid,
                'action_time': datetime.datetime.now()
            })

            for order in self.sale_orders.all():
                if order.is_deposit() and order.status == SaleTrade.WAIT_SELLER_SEND_GOODS:
                    order.status = SaleTrade.TRADE_FINISHED
                    order.save(update_fields=['status'])
            st = SaleTrade.objects.get(id=self.id)
            st.confirm_payment()
            st.set_order_paid()

        except Exception, exc:
            logger.error({
                'action': 'trade_confirm_error',
                'action_time': datetime.datetime.now(),
                'order_no': self.tid,
                'message': str(exc),
                'traceback': traceback.format_exc(),
            })
            raise exc

        logger.info({
            'action': 'trade_confirm_end',
            'order_no': self.tid,
            'charge': charge,
            'pay_time': charge_time,
            'action_time': datetime.datetime.now()
        })

    def pay_confirm(self):
        # 暂时用此方法替代charge_confirm进行测试
        # 测试时忽略了charge
        from shopback.trades.models import SkuStock
        self.status = self.WAIT_SELLER_SEND_GOODS
        self.pay_time = datetime.datetime.now()
        self.save()
        for so in self.sale_orders.all():
            so.set_status_paid(self.pay_time)
            SkuStock.set_order_paid_num(so.sku_id, so.num)
        self.set_order_paid()

    def set_order_paid(self):
        if self.order_type == SaleTrade.SALE_ORDER:
            for so in self.sale_orders.all():
                so.set_psi_paid()
        self.update_teambuy()
        from shopback.trades.apis.v1.packet import packing_skus
        packing_skus()

    def redeliver_sku_item(self, old_sale_order):
        sku = ProductSku.objects.get(id=old_sale_order.sku_id)
        old_sale_order.status = SaleOrder.TRADE_CLOSED_BY_SYS
        new_sku_id = old_sale_order.sku_id
        new_num = old_sale_order.num
        print old_sale_order.id
        old_sale_order.save()
        if old_sale_order.status == SaleOrder.WAIT_SELLER_SEND_GOODS:
            old_sale_order.set_psi_cancel()

        new_sale_order = old_sale_order
        new_sale_order.id = None
        cnt = 1
        old_sale_order_oid = old_sale_order.oid
        if '-' in old_sale_order.oid:
            cnt = self.sale_orders.filter(oid__startswith=old_sale_order.oid).count()
            old_sale_order_oid = old_sale_order.oid.split('-')[0]
        new_sale_order.oid = '%s-%s' % (old_sale_order_oid, str(cnt))
        new_sale_order.status = SaleOrder.WAIT_SELLER_SEND_GOODS
        new_sale_order.sku_id = new_sku_id
        product = sku.product
        new_sale_order.outer_id = product.outer_id
        new_sale_order.outer_sku_id = sku.outer_id
        new_sale_order.num = new_num
        new_sale_order.sku_name = sku.properties_alias
        new_sale_order.title = product.name
        new_sale_order.pic_path = product.pic_path
        new_sale_order.pay_time = old_sale_order.pay_time
        new_sale_order.refund_id = None
        new_sale_order.refund_fee = 0
        new_sale_order.refund_status = SaleRefund.NO_REFUND
        new_sale_order.save()
        new_sale_order.set_psi_paid()

    def change_sku_item(self, old_sale_order, sku_id, num=1):
        """
            更换sku
        :param old_sale_order:
        :return:
        """

        if not old_sale_order.can_change_sku():
            raise Exception(u'已发货或退款的商品不能执行换货')
        sku = ProductSku.objects.get(id=sku_id)
        # from shopback.items.models import SkuStock
        # sku_stock = SkuStock.objects.get(sku_id=sku_id)
        # if sku_stock.realtime_quantity < num:
        #     raise Exception(u'换货数必须小于实时库存')
        old_sale_order.status = SaleOrder.TRADE_CLOSED_BY_SYS
        old_sale_order.save()
        old_sale_order.set_psi_cancel()
        new_sale_order = old_sale_order
        new_sale_order.id = None
        cnt = self.sale_orders.count()
        new_sale_order.oid = '%s-%s' % (old_sale_order.oid.split('-')[0], str(cnt))
        new_sale_order.status = SaleOrder.WAIT_SELLER_SEND_GOODS
        new_sale_order.sku_id = sku_id
        product = sku.product
        new_sale_order.outer_id = product.outer_id
        new_sale_order.outer_sku_id = sku.outer_id
        new_sale_order.num = num
        new_sale_order.sku_name = sku.properties_alias
        new_sale_order.title = product.name
        new_sale_order.pic_path = product.pic_path
        new_sale_order.pay_time = old_sale_order.pay_time
        new_sale_order.refund_id = None
        new_sale_order.refund_fee = 0
        new_sale_order.refund_status = SaleRefund.NO_REFUND
        new_sale_order.save()
        new_sale_order.set_psi_paid()

    def reissue_order_by_incomplete_refund(self, old_sale_order, num):
        # type: (SaleOrder, int) -> SaleOrder
        """补发 不完全 退款的 订单
        """
        from copy import deepcopy

        new_sale_order = deepcopy(old_sale_order)
        new_sale_order.id = None
        cnt = self.sale_orders.count()
        new_sale_order.oid = '%s-%s' % (old_sale_order.oid.split('-')[0], str(cnt))
        new_sale_order.status = SaleOrder.WAIT_SELLER_SEND_GOODS
        new_sale_order.num = num
        payment = float('%.2f' % (old_sale_order.payment / old_sale_order.num)) * num
        discount_fee = float('%.2f' % (old_sale_order.discount_fee / old_sale_order.num)) * num
        new_sale_order.payment = payment
        new_sale_order.discount_fee = discount_fee
        new_sale_order.refund_id = None
        new_sale_order.refund_status = 0
        new_sale_order.refund_fee = 0
        new_sale_order.save()
        new_sale_order.set_psi_paid()

    @transaction.atomic
    def close_trade(self):
        """ 关闭待付款订单 """
        st = SaleTrade.objects.select_for_update().get(id=self.id)
        if st.status != SaleTrade.WAIT_BUYER_PAY:
            return

        st.status = SaleTrade.TRADE_CLOSED_BY_SYS
        st.save()

        for order in st.normal_orders:
            order.close_order()

        if st.has_budget_paid:
            ubudget = UserBudget.objects.get(user=st.buyer_id)
            ubudget.charge_cancel(st.id)

        if st.has_coin_paid:
            from flashsale.xiaolumm.models import XiaoluCoin, XiaoluCoinLog
            customer = Customer.objects.filter(id=self.buyer_id).first()
            xlmm     = customer.getXiaolumm()
            xiaolucoin = XiaoluCoin.objects.select_for_update().filter(mama_id=xlmm.id).first()
            # 必须该订单有小鹿币消费记录，才能退款到小鹿币钱包
            consume_log   = XiaoluCoinLog.objects.filter(subject=XiaoluCoinLog.CONSUME, referal_id=self.id).first()
            if xiaolucoin and consume_log:
                xiaolucoin.refund(self.coin_payment, self.id)

        # 释放被当前订单使用的优惠券
        st.release_coupon()

    def release_coupon(self):
        """ 释放订单对应的优惠券 """
        # from flashsale.coupon.apis.v1.usercoupon import rollback_user_coupon_status_2_unused_by_ids
        from flashsale.coupon.apis.v1.transfer import cancel_transfer_record_by_trade

        # coupon_ids = self.extras_info.get("coupon") or []
        # if isinstance(coupon_ids, str):
        #     coupon_ids = coupon_ids.strip()
        #     coupon_ids = [int(coupon_ids)] if coupon_ids.isdigit() else []
        # coupon_ids = [int(i) for i in coupon_ids]
        # if coupon_ids:
        # rollback_user_coupon_status_2_unused_by_ids(coupon_ids) # 修改该优惠券的状态到未使用
        cancel_transfer_record_by_trade(self.tid)  # 将对应的流通券记录取消掉

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
        product_ids = self.sale_orders.values_list('item_id', flat=True)
        for product_id in product_ids:
            product = Product.objects.filter(id=product_id).first()
            if product and ware_by is None:
                ware_by = product.ware_by
                continue
            if product:
                ware_by &= product.ware_by
        return ware_by or WARE_NONE

    @property
    def package_orders(self):
        package_list = []
        for sorder in self.sale_orders.all():
            package = sorder.package_order
            if package and package not in package_list:
                package_list.append(package)
        return package_list

    def update_teambuy(instance):
        if instance.order_type == SaleTrade.TEAMBUY_ORDER and instance.pay_time:
            from flashsale.pay.models import TeamBuy, TeamBuyDetail
            if not TeamBuyDetail.objects.filter(tid=instance.tid).first():
                TeamBuy.create_or_join(instance)


# def add_renew_deposit_record(sender, obj, **kwargs):
#     """
#     押金续费:　使用代理钱包混合支付的情况
#     """
#     if not obj.is_Deposite_Order():
#         return
#     wallet_renew_deposit = obj.extras_info.get('wallet_renew_deposit') or 0
#     if float(wallet_renew_deposit) <= 0:  # 不是续费类型的
#         return
#     order = obj.sale_orders.all().first()
#     if order.is_1_deposit():
#         return
#
#     from flashsale.xiaolumm.models import CashOut, XiaoluMama, MamaFortune
#     from core.options import log_action, ADDITION
#     from flashsale.pay.models import ProductSku
#
#     sku = ProductSku.objects.get(id=order.sku_id)
#     deposit_price = sku.agent_price
#
#     customer = Customer.objects.get(id=obj.buyer_id)
#     xlmm = XiaoluMama.objects.filter(openid=customer.unionid).first()
#     cash = deposit_price - order.payment
#     if cash <= 0:
#         return
#
#     cash_value = cash * 100
#
#     cash = CashOut.create(xlmm.id, cash_value, CashOut.MAMA_RENEW)
#     cash.approve_cashout()
#
#     log_action(customer.user, cash, ADDITION, u'用户妈妈钱包兑换代理续费')
#
#
# signal_saletrade_pay_confirm.connect(add_renew_deposit_record, sender=SaleTrade,
#                                      dispatch_uid=u'trade_pay_confirm_add_renew_deposit_record')


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


def trigger_mama_deposit_action(sender, obj, *args, **kwargs):
    """根据押金订单处理妈妈记录:
    """
    if not (obj.status == SaleTrade.WAIT_SELLER_SEND_GOODS and obj.is_Deposite_Order()):
        return
    try:
        from flashsale.xiaolumm.apis.v1.xiaolumama import mama_pay_deposit
        order = obj.sale_orders.first()
        if order.is_1_deposit():
            deposit_type = 1
        elif order.is_99_deposit():
            deposit_type = 99
        elif order.is_188_deposit():
            deposit_type = 188
        else:
            return
        referrer = int(str(obj.extras_info.get('mm_linkid', '')).strip() or '0' if obj.extras_info else '0')  # 推荐人id
        order.status = SaleTrade.TRADE_FINISHED
        order.save(update_fields=['status'])
        mama_pay_deposit(obj.buyer_id, deposit_type, referrer, obj.id, oid=order.oid)
    except Exception as e:
        logging.error(e)


signal_saletrade_pay_confirm.connect(trigger_mama_deposit_action,
                                     sender=SaleTrade,
                                     dispatch_uid="signal_trigger_mama_deposit_action")


def update_customer_first_paytime(sender, obj, **kwargs):
    """
    订单支付后，检测用户是否第一次购买，如果是，更新用户第一次购买时间
    """
    saletrade = obj
    customer = saletrade.order_buyer
    if not customer.first_paytime:
        customer.first_paytime = saletrade.pay_time
        customer.save()


signal_saletrade_pay_confirm.connect(update_customer_first_paytime, sender=SaleTrade)


def update_skustock_paid_num(sender, obj, **kwargs):
    """
    订单支付后，检测用户是否第一次购买，如果是，更新用户第一次购买时间
    """
    from shopback.trades.models import SkuStock
    for order in obj.sale_orders.all():
        SkuStock.set_order_paid_num(order.sku_id, order.num)


signal_saletrade_pay_confirm.connect(update_skustock_paid_num, sender=SaleTrade)


def push_trade_pay_notify(sender, obj, **kwargs):
    """
    订单支付成功推送
    """
    if True:
        return
    from flashsale.push.tasks import task_push_trade_pay_notify
    saletrade = obj
    customer = saletrade.order_buyer
    if customer.unionid:
        task_push_trade_pay_notify.delay(obj)


signal_saletrade_pay_confirm.connect(push_trade_pay_notify, sender=SaleTrade)


def tongji_trade_source(sender, obj, **kwargs):
    """
    统计付款订单来源，发送到 OneAPM
    1. 来自小鹿妈妈或者小鹿妈妈分享的链接
    2. 来自直接购买
    """
    from flashsale.pay.tasks import task_tongji_trade_source
    task_tongji_trade_source.delay()


signal_saletrade_pay_confirm.connect(tongji_trade_source, sender=SaleTrade)


def tongji_trade_pay_channel(sender, obj, **kwargs):
    """
    统计订单支付方式：微信，支付宝等
    """
    from django_statsd.clients import statsd

    channel = obj.channel
    now = datetime.datetime.today()
    today = datetime.datetime(now.year, now.month, now.day)

    key = 'xiaolumm.paychannel_from_%s' % channel
    trades_count = SaleTrade.objects.filter(pay_time__gte=today, channel=channel).count()
    statsd.gauge(key, trades_count)


signal_saletrade_pay_confirm.connect(tongji_trade_pay_channel, sender=SaleTrade)


def set_coupon_2_use_by_trade_confirm(sender, obj, **kwargs):
    """订单支付成功设置优惠券为使用状态
    """
    try:
        coupon_ids = obj.extras_info.get('coupon') or []
        logger.info({
            'action': 'set_coupon_2_use_by_trade_confirm_start',
            'coupon_ids': ','.join([str(i) for i in coupon_ids]),
            'order_no': obj.tid,
            'action_time': datetime.datetime.now()
        })
        if not coupon_ids:
            return
        coupon_ids = [int(c) for c in coupon_ids]
        from flashsale.coupon.apis.v1.usercoupon import use_coupon_by_ids, get_user_coupons_by_ids
        from flashsale.coupon.models import CouponTransferRecord
        from flashsale.coupon.apis.v1.transfercoupondetail import create_transfer_coupon_detail

        coupons = get_user_coupons_by_ids(coupon_ids)
        use_coupon_by_ids(coupon_ids, obj.tid)  # 使用优惠券

        # 创建 消费流通记录 如果是流通券类型的话
        template_id = None
        for coupon in coupons:
            if coupon.is_transfer_coupon():
                template_id = coupon.template_id
                break
        if template_id:
            coupon_num = len(coupon_ids)
            transfer = CouponTransferRecord.create_consume_record(coupon_num, obj, template_id)
            create_transfer_coupon_detail(transfer.id, coupon_ids)

        logger.info({
            'action': 'set_coupon_2_use_by_trade_confirm_end',
            'action_time': datetime.datetime.now(),
            'coupons': coupons.values('id', 'status'),
            'order_no': obj.tid,
        })
    except Exception as e:
        logger.warn({
            'action': 'set_coupon_2_use_by_trade_confirm_error',
            'order_no': obj.tid,
            'action_time': datetime.datetime.now(),
            'traceback': traceback.format_exc(),
        })


signal_saletrade_pay_confirm.connect(set_coupon_2_use_by_trade_confirm, sender=SaleTrade,
                                     dispatch_uid='signal_set_coupon_2_use_by_trade_confirm')


def update_teambuy(sender, instance, created, **kwargs):
    transaction.on_commit(lambda: instance.update_teambuy())


post_save.connect(update_teambuy, sender=SaleTrade, dispatch_uid='post_save_saletrade_update_teambuy')


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

    item_id = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'商品ID')
    title = models.CharField(max_length=128, blank=True, verbose_name=u'商品标题')
    price = models.FloatField(default=0.0, verbose_name=u'商品单价')

    sku_id = models.CharField(max_length=20, db_index=True, blank=True, verbose_name=u'属性编码')
    num = models.IntegerField(null=True, default=0, verbose_name=u'商品数量')

    outer_id = models.CharField(max_length=32, blank=True, verbose_name=u'商品外部编码')
    outer_sku_id = models.CharField(max_length=32, blank=True, verbose_name=u'规格外部编码')

    total_fee = models.FloatField(default=0.0, verbose_name=u'总费用')
    payment = models.FloatField(default=0.0, verbose_name=u'实付款')
    discount_fee = models.FloatField(default=0.0, verbose_name=u'优惠金额')

    sku_name = models.CharField(max_length=256, blank=True, verbose_name=u'购买规格')
    pic_path = models.CharField(max_length=512, blank=True, verbose_name=u'商品图片')

    pay_time = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'付款日期')
    consign_time = models.DateTimeField(null=True, blank=True, verbose_name=u'发货日期')
    sign_time = models.DateTimeField(null=True, blank=True, verbose_name=u'签收日期')

    refund_id = models.BigIntegerField(null=True, verbose_name=u'退款ID')
    refund_fee = models.FloatField(default=0.0, verbose_name=u'退款费用')
    refund_status = models.IntegerField(choices=SaleRefund.REFUND_STATUS,
                                        default=SaleRefund.NO_REFUND,
                                        blank=True, verbose_name=u'退款状态')

    status = models.IntegerField(choices=ORDER_STATUS, default=TRADE_NO_CREATE_PAY,
                                 db_index=True, blank=True, verbose_name=u'订单状态')
    extras = JSONCharMyField(blank=True, default=default_extras, verbose_name=u'附加信息')

    def __unicode__(self):
        return '<%s>' % (self.id)

    def can_change_sku(self):
        if self.status != SaleOrder.WAIT_SELLER_SEND_GOODS \
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
        refund = SaleRefund.objects.filter(trade_id=self.sale_trade.id, order_id=self.id).first()
        return refund

    @property
    def package_order(self):
        if not hasattr(self, '_package_order_'):
            from shopback.trades.models import PackageOrder
            package_sku_item = self.package_sku
            if package_sku_item and package_sku_item.package_order_id:
                self._package_order_ = PackageOrder.objects.filter(id=package_sku_item.package_order_id).first()
            else:
                self._package_order_ = None
        return self._package_order_

    def is_packaged(self):
        """ 是否打包 """
        from shopback.trades.models import PackageSkuItem
        package_sku_item = self.package_sku
        if package_sku_item and package_sku_item.assign_status != PackageSkuItem.NOT_ASSIGNED and package_sku_item.package_order_id:
            return True
        return False

    def is_post(self):
        """是否发货
        """
        from shopback.trades.models import PackageSkuItem
        return self.package_sku and self.package_sku.assign_status == PackageSkuItem.FINISHED

    @property
    def refundable(self):
        return self.get_refundable()

    def set_status_paid(self, pay_time):
        from shopback.trades.models import SkuStock
        self.status = self.WAIT_SELLER_SEND_GOODS
        self.pay_time = pay_time
        self.save()

    def finish_sent(self):
        self.status = SaleOrder.WAIT_BUYER_CONFIRM_GOODS
        self.consign_time = datetime.datetime.now()
        self.save()

    def set_psi_paid(self):
        from shopback.trades.models import PackageSkuItem
        if self.sale_trade.order_type in [SaleTrade.RESERVE_ORDER, SaleTrade.DEPOSITE_ORDER,
                                          SaleTrade.ELECTRONIC_GOODS_ORDER]:
            return
        if self.is_teambuy() and not self.teambuy_can_send():
            return
        if not PackageSkuItem.objects.filter(sale_order_id=self.id).exists():
            psi = PackageSkuItem.create(self)

    def set_psi_cancel(self):
        if self.package_sku:
            self.package_sku.set_status_cancel()

    def is_teambuy(self):
        return self.sale_trade.order_type == SaleTrade.TEAMBUY_ORDER

    def teambuy_can_send(self):
        from flashsale.pay.models import TeamBuyDetail
        oid = self.oid.split('-')[0]  # 应对重新发货
        return TeamBuyDetail.objects.get(oid=oid).teambuy.status == 1

    def can_refund(self):
        return self.get_refundable()

    def get_refundable(self):
        # return self.sale_trade.status in SaleTrade.REFUNDABLE_STATUS?
        if self.status not in (SaleOrder.WAIT_SELLER_SEND_GOODS, SaleOrder.TRADE_BUYER_SIGNED):
            return False
        if self.is_deposit() and self.sale_trade.status not in SaleTrade.REFUNDABLE_STATUS:
            return False
        if self.sale_trade.order_type == SaleTrade.TEAMBUY_ORDER and self.status in (SaleOrder.WAIT_SELLER_SEND_GOODS,):
            return False  # 团购订单　在付款状态不能退款
        return True

    def calculate_refund_fee(self, num):
        # type: (int) -> float
        """计算退款费用　
        """

        def fake_round(x, y):
            # type: (float, int) -> float
            return int(x / float(y) * 100) * 0.01

        if num == 0:  # 提交的退款产品数量为0
            return 0
        elif num == self.num:  # 退款数量等于购买数量 全额退款
            apply_fee = self.payment  # 申请费用
        else:
            apply_fee = fake_round(self.payment, self.num) * num
        return apply_fee

    def do_refund(self, refund_channel, reason=0, refund_num=None, refund_fee=None, good_status=None,
                  desc='', proof_pic=None, creator=None):
        # type: (int, Any, Any, Any, text_type, Any, text_type) -> SaleRefund
        """订单退款
        """
        from shopback.refunds.models import REFUND_REASON
        from flashsale.pay.models import SaleRefund
        reason = REFUND_REASON[reason][1]
        # 如果是发货或者确认签收状态则为　买家收到货
        if good_status is None:
            if self.status in (SaleOrder.WAIT_BUYER_CONFIRM_GOODS, SaleOrder.TRADE_BUYER_SIGNED):
                good_status = SaleRefund.BUYER_RECEIVED
            elif self.status == SaleOrder.WAIT_SELLER_SEND_GOODS:  # 已付款
                good_status = SaleRefund.BUYER_NOT_RECEIVED  # 没有收到货
            else:
                raise Exception(u'订单状态不予退款操作!')
        refund_num = refund_num if refund_num else self.num
        refund_fee = refund_fee if refund_fee else self.payment
        salerefund = SaleRefund.create_salerefund(self, refund_num, refund_fee, reason, good_status,
                                                  desc=desc, refund_channel=refund_channel, proof_pic=proof_pic,
                                                  creator=creator)
        return salerefund

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

        delta_days = consign_time and (now_time - consign_time).days or 0  # 距离发货天数

        if (self.status == self.WAIT_BUYER_CONFIRM_GOODS  # 等待签收
            and (delta_days > CONST.ORDER_WAIT_CONFIRM_TO_FINISHED_DAYS)):  # 发货超过14天
            return True
        elif (self.status == self.TRADE_BUYER_SIGNED  # 已经签收
              and (not sign_time
                   or (now_time - sign_time).days > CONST.ORDER_SIGNED_TO_FINISHED_DAYS  # 签收超过7天
                   or delta_days > CONST.ORDER_WAIT_CONFIRM_TO_FINISHED_DAYS)):  # 发货超过14天
            return True
        return False

    def close_order(self):
        """ 待付款关闭订单 """
        self.status = self.TRADE_CLOSED_BY_SYS
        self.save()
        # sku = get_object_or_404(ProductSku, pk=self.sku_id)
        # Product.objects.releaseLockQuantity(sku, self.num)

    def confirm_sign_order(self):
        """确认签收 修改该订单状态到 确认签收状态"""
        if self.status != SaleOrder.WAIT_BUYER_CONFIRM_GOODS:
            raise Exception('没有发货不能签收')
        self.status = SaleOrder.TRADE_BUYER_SIGNED
        self.sign_time = datetime.datetime.now()
        self.save(update_fields=['status', 'sign_time'])
        self.package_sku.set_status_finish()
        sale_trade = self.sale_trade
        unsign_orders = sale_trade.normal_orders.exclude(
            status__in=(SaleOrder.TRADE_BUYER_SIGNED, SaleOrder.TRADE_FINISHED))
        if not unsign_orders.exists():
            sale_trade.status = SaleTrade.TRADE_BUYER_SIGNED
            sale_trade.save(update_fields=['status'])

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

    def need_send(self):
        if self.is_teambuy():
            return self.teambuy_can_send()
        else:
            return self.status == SaleOrder.WAIT_SELLER_SEND_GOODS and self.refund_status <= SaleRefund.REFUND_REFUSE_BUYER

    def is_pending(self):
        if self.is_teambuy():
            return self.teambuy_can_send()
        else:
            return self.status == SaleOrder.WAIT_SELLER_SEND_GOODS and self.refund_status <= SaleRefund.REFUND_REFUSE_BUYER

    def is_finished(self):
        return self.status == SaleOrder.TRADE_FINISHED

    def is_confirmed(self):
        return self.status >= SaleOrder.WAIT_BUYER_CONFIRM_GOODS and \
               self.status <= SaleOrder.TRADE_FINISHED and \
               self.refund_status <= SaleRefund.REFUND_REFUSE_BUYER

    def is_canceled(self):
        return self.status > SaleOrder.TRADE_FINISHED or \
               self.refund_status > SaleRefund.REFUND_REFUSE_BUYER

    def is_deposit(self):
        return self.outer_id.startswith('RMB')

    def is_transfer_coupon(self):
        return self.is_deposit() and \
               (self.outer_sku_id != '1' and self.outer_sku_id != '2' and self.outer_sku_id != '3') \
               and (not self.is_recharge_deposit())

    def is_1_deposit(self):
        return self.is_deposit() and self.outer_sku_id == '3'

    def is_99_deposit(self):
        return self.is_deposit() and self.outer_sku_id == '2'

    def is_188_deposit(self):
        return self.is_deposit() and self.outer_sku_id == '1'

    def is_new_elite_deposit(self):
        return self.is_deposit() and (self.outer_sku_id == '338' or self.outer_sku_id == '216')

    def is_recharge_deposit(self):
        return self.is_deposit() and (self.outer_sku_id == '600' or self.outer_sku_id == '3000'
                                      or self.outer_sku_id == '9000' or self.outer_sku_id == '25000'
                                      or self.outer_sku_id == '80000')

    def is_elite_365_order(self):
        return self.item_product.model_id == 25408

    @property
    def item_product(self):
        if not hasattr(self, '_item_product_'):
            self._item_product_ = Product.objects.filter(id=self.item_id).first()
        return self._item_product_

    @property
    def item_ware_by(self):
        """　商品所属仓库 """
        product = Product.objects.filter(id=self.item_id).first()
        if product:
            ware_by = product.ware_by
            return ware_by
        return WARE_NONE

    def stats_post_goods(self):
        return self.status in (SaleOrder.WAIT_BUYER_CONFIRM_GOODS,
                               SaleOrder.TRADE_BUYER_SIGNED,
                               SaleOrder.TRADE_FINISHED)

    def stats_not_pay(self):
        return self.status in (SaleOrder.TRADE_NO_CREATE_PAY,
                               SaleOrder.WAIT_BUYER_PAY,
                               SaleOrder.TRADE_CLOSED_BY_SYS)

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

    @property
    def package_sku(self):
        if not hasattr(self, '_package_sku_'):
            from shopback.trades.models import PackageSkuItem
            self._package_sku_ = PackageSkuItem.objects.filter(sale_order_id=self.id).first()
        return self._package_sku_

    @property
    def product_sku(self):
        if not hasattr(self, '_product_sku_'):
            from flashsale.pay.models import ProductSku
            self._product_sku_ = ProductSku.objects.filter(id=self.sku_id).first()
        return self._product_sku_

    @property
    def product(self):
        return self.product_sku.product


@receiver(post_save, sender=SaleOrder, dispatch_uid='post_save_saleorder_notify_update')
def saleorder_notify_update(sender, instance, created, raw, **kwargs):
    from flashsale.pay.tasks import task_saleorder_post_update_send_signal

    def _trans_commit_send_signal():
        logger.info({
            'action': 'saleorder_post_save_commit',
            'action_time': datetime.datetime.now(),
            'order_oid': instance.oid,
        })
        task_saleorder_post_update_send_signal.delay(
            instance.id,
            created,
            raw
        )

    transaction.on_commit(_trans_commit_send_signal)


@receiver(signal_saleorder_post_update, sender=SaleOrder, dispatch_uid='post_save_order_trigger')
def post_save_order_trigger(sender, instance, created, raw, **kwargs):
    """
    SaleOrder save triggers adding carry to OrderCarry.
    """
    if raw:
        return

    from flashsale.coupon.apis.v1.transfer import send_order_transfer_coupons
    from flashsale.xiaolumm.tasks import task_update_referal_relationship, task_order_trigger
    from flashsale.coupon.apis.v1.transfer import send_new_elite_transfer_coupons, elite_mama_recharge, create_new_elite_mama, give_gift_score_to_new_elite_mama

    def _order_trigger(instance):
        message = 'OK'
        logger.info({
            'action': 'task_order_trigger_start',
            'action_time': datetime.datetime.now(),
            'order_oid': instance.oid,
            'order_status': instance.status,
        })
        try:
            if instance.is_deposit():
                if instance.is_confirmed():
                    if instance.is_1_deposit():  # 一元开店 不记录推荐关系
                        return
                    if instance.is_transfer_coupon():
                        send_order_transfer_coupons(instance.sale_trade.buyer_id, instance.id,
                                                    instance.oid, instance.num, instance.item_id)
                        return
                    if instance.is_recharge_deposit():
                        elite_mama_recharge(instance.sale_trade.buyer_id, instance.id,
                                            instance.oid, instance.item_id)
                        return
                    task_update_referal_relationship(instance)
            else:
                # 365 order create relationship and first give 60 score
                if instance.is_elite_365_order() and SaleOrder.WAIT_SELLER_SEND_GOODS <= instance.status <= SaleOrder.TRADE_FINISHED:
                    customer = Customer.objects.get(id=instance.sale_trade.buyer_id)
                    to_mama = customer.get_xiaolumm()
                    uni_key = "gift-365elite-in-%s" % (to_mama.id)
                    from flashsale.coupon.models.transfer_coupon import CouponTransferRecord
                    gift_cts = CouponTransferRecord.objects.filter(uni_key=uni_key).first()
                    # 判断妈妈为一个新妈妈，满足条件如下：妈妈还不是精英妈妈；
                    from flashsale.xiaolumm.models.models import XiaoluMama
                    if (not to_mama.is_elite_mama) or (not gift_cts):
                        create_new_elite_mama(customer, to_mama, instance)
                        give_gift_score_to_new_elite_mama(customer, to_mama, instance)
                task_order_trigger(instance)
        except Exception, exc:
            message = traceback.format_exc(),
        logger.info({
            'action': 'task_order_trigger_end',
            'action_time': datetime.datetime.now(),
            'order_oid': instance.oid,
            'order_status': instance.status,
            'traceback': message,
        })

    transaction.on_commit(lambda: _order_trigger(instance))


# @receiver(signal_saleorder_post_update, sender=SaleOrder, dispatch_uid='post_save_update_package_sku_item')
def update_package_sku_item(sender, instance, created, **kwargs):
    """ 更新PackageSkuItem状态 """
    if instance.created > datetime.datetime(2016, 4, 21) and instance.status >= SaleOrder.WAIT_SELLER_SEND_GOODS and \
                    instance.sale_trade.order_type == SaleTrade.SALE_ORDER:
        from flashsale.pay.tasks import task_saleorder_update_package_sku_item
        task_saleorder_update_package_sku_item.delay(instance)


# if not settings.CLOSE_CELERY:
#     post_save.connect(update_package_sku_item, sender=SaleOrder, dispatch_uid='post_save_update_package_sku_item')


def saleorder_update_productskustats_waitingpay_num(sender, instance, *args, **kwargs):
    from shopback.items.tasks_stats import task_saleorder_update_productskustats_waitingpay_num
    transaction.on_commit(lambda: task_saleorder_update_productskustats_waitingpay_num(instance.sku_id))


if not settings.CLOSE_CELERY:
    signal_saleorder_post_update.connect(saleorder_update_productskustats_waitingpay_num, sender=SaleOrder,
                                         dispatch_uid='post_save_aleorder_update_productskustats_waitingpay_num')


def saleorder_update_saletrade_status(sender, instance, *args, **kwargs):
    if instance.status > SaleOrder.WAIT_BUYER_PAY:
        from flashsale.pay.tasks import tasks_update_sale_trade_status
        transaction.on_commit(lambda: tasks_update_sale_trade_status(instance.sale_trade_id))


signal_saleorder_post_update.connect(saleorder_update_saletrade_status, sender=SaleOrder,
                                     dispatch_uid='post_save_saleorder_update_saletrade_status')


def saleorder_update_stats_record(sender, instance, *args, **kwargs):
    from statistics.tasks import task_update_sale_order_stats_record
    transaction.on_commit(lambda: task_update_sale_order_stats_record.delay(instance))


signal_saleorder_post_update.connect(saleorder_update_stats_record, sender=SaleOrder,
                                     dispatch_uid='post_save_saleorder_update_stats_record')


class SaleOrderSyncLog(BaseModel):
    UNKNOWN = 0
    SO_PSI = 1  # SaleOrder -> PackageSkuItem
    PSI_PR = 2  # PackageSkuItem -> PurchaseRecord
    BOOKNUM = 3
    PACKAGE_SKU_NUM = 4  # PackageSkuItem -> PackageOrder
    INBOUND_OUT_STOCK = 5  # InBoundDetail -> InBound out_stock
    INBOUND_INFERIOR = 6  # InBoundDetail -> InBound inferior
    PACKAGE_SKU_FINISH_NUM = 7
    PACKAGE_ASSIGN_NUM = 8
    PACKAGE_STOCK_NOTASSIGN = 9
    SALE_ORDER_SHOPPING_CART = 10
    SALE_ORDER_WAITING_PAY = 11
    TYPE_CHOICE = ((UNKNOWN, u'未知'), (SO_PSI, u'发货PSI'), (PSI_PR, u'订货PR'), (BOOKNUM, u'订货NUM'),
                   (PACKAGE_SKU_FINISH_NUM, u'包裹商品完成计数'), (INBOUND_OUT_STOCK, u'入库有多货'),
                   (INBOUND_INFERIOR, u'入库有次品'), (PACKAGE_SKU_NUM, u'包裹商品实时计数'),
                   (PACKAGE_ASSIGN_NUM, u'备货计数'), (PACKAGE_STOCK_NOTASSIGN, u'有库存未备货'),
                   (SALE_ORDER_SHOPPING_CART, u'购物车订单数'), (SALE_ORDER_WAITING_PAY, u'待支付订单数'))
    OPEN = 1
    COMPLETED = 2
    STATUS_CHOICE = ((OPEN, u'未完成'), (COMPLETED, u'完成'))
    time_from = models.DateTimeField(verbose_name=u'开始时间')
    time_to = models.DateTimeField(verbose_name=u'结束时间')
    uni_key = models.CharField(max_length=32, unique=True, verbose_name='UniKey')
    target_num = models.IntegerField(null=True, default=0, verbose_name=u'目标数量')
    actual_num = models.IntegerField(null=True, default=0, verbose_name=u'实际数量')
    type = models.IntegerField(choices=TYPE_CHOICE, default=UNKNOWN, db_index=True, verbose_name=u'类型')
    status = models.IntegerField(choices=STATUS_CHOICE, default=OPEN, db_index=True, verbose_name=u'状态')

    class Meta:
        db_table = 'flashsale_saleorder_synclog'
        app_label = 'pay'
        verbose_name = u'v2/同步检查日志'
        verbose_name_plural = u'v2/同步检查日志表'

    def __unicode__(self):
        return '%s|%s' % (self.id, self.uni_key)

    def is_completed(self):
        return self.target_num == self.actual_num


def post_save_gauge_data(sender, instance, created, **kwargs):
    from django_statsd.clients import statsd
    key = None
    if instance.is_completed():
        if instance.type == SaleOrderSyncLog.SO_PSI:
            key = 'saleorder_synclog.psi'
        if instance.type == SaleOrderSyncLog.PSI_PR:
            key = 'saleorder_synclog.pr'
        if instance.type == SaleOrderSyncLog.BOOKNUM:
            key = 'saleorder_synclog.booknum'
        if instance.type == SaleOrderSyncLog.PACKAGE_SKU_FINISH_NUM:
            key = "saleorder_synclog.package_sku_finish_count"
        if instance.type == SaleOrderSyncLog.PACKAGE_SKU_NUM:
            key = "saleorder_synclog.package_sku_count"
        if instance.type == SaleOrderSyncLog.INBOUND_OUT_STOCK:
            key = "saleorder_synclog.inbound_out_stock"
        if instance.type == SaleOrderSyncLog.INBOUND_INFERIOR:
            key = "saleorder_synclog.inbound_inferior"
        if instance.type == SaleOrderSyncLog.PACKAGE_STOCK_NOTASSIGN:
            key = "saleorder_synclog.package_stock_notassign"
        if instance.type == SaleOrderSyncLog.PACKAGE_ASSIGN_NUM:
            key = "saleorder_synclog.package_assign_num"
        if key:
            statsd.gauge(key, instance.actual_num)
            # logger.warn("gauge_data|key:%s,completed:%s, actual_num:%s" % (key, instance.is_completed(), instance.actual_num))


signal_saleorder_post_update.connect(post_save_gauge_data, sender=SaleOrderSyncLog, dispatch_uid='post_save_gauge_data')


def add_order_integral(sender, instance, created, **kwargs):
    from flashsale.pay.tasks import task_add_user_order_integral
    transaction.on_commit(lambda: task_add_user_order_integral.delay(instance))


signal_saleorder_post_update.connect(add_order_integral, sender=SaleOrder, dispatch_uid='post_save_add_order_integral')
