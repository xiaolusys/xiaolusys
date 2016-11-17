# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import datetime
from django.db import models
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.db.models import F

from shopback.categorys.models import CategorySaleStat
from common.modelutils import update_model_fields
from core.fields import JSONCharMyField

from shopback import paramconfig as pcfg
from shopback.items.models import Product
from supplychain.supplier.models import SaleProduct
from flashsale.pay.signals import signal_saletrade_refund_post
from flashsale.pay import NO_REFUND, REFUND_CLOSED, REFUND_REFUSE_BUYER, REFUND_WAIT_SELLER_AGREE, \
    REFUND_WAIT_RETURN_GOODS, REFUND_CONFIRM_GOODS, REFUND_APPROVE, REFUND_SUCCESS
from shopback.warehouse.constants import WARE_THIRD, WARE_SH, WARE_GZ, WARE_COMPANY
from ..signals import signal_saletrade_refund_confirm
from ..options import uniqid
from .base import PayBaseModel
from .. import constants

import pingpp
import logging

pingpp.api_key = settings.PINGPP_APPKEY
logger = logging.getLogger(__name__)


def default_refund_no():
    return uniqid('RF%s' % (datetime.datetime.now().strftime('%y%m%d')))


class SaleRefund(PayBaseModel):
    NO_REFUND = NO_REFUND
    REFUND_CLOSED = REFUND_CLOSED
    REFUND_REFUSE_BUYER = REFUND_REFUSE_BUYER
    REFUND_WAIT_SELLER_AGREE = REFUND_WAIT_SELLER_AGREE
    REFUND_WAIT_RETURN_GOODS = REFUND_WAIT_RETURN_GOODS
    REFUND_CONFIRM_GOODS = REFUND_CONFIRM_GOODS
    REFUND_APPROVE = REFUND_APPROVE
    REFUND_SUCCESS = REFUND_SUCCESS

    REFUND_STATUS = (
        (NO_REFUND, u'没有退款'),
        (REFUND_WAIT_SELLER_AGREE, u'退款待审'),
        (REFUND_WAIT_RETURN_GOODS, u'同意申请'),
        (REFUND_CONFIRM_GOODS, u'退货待收'),
        (REFUND_REFUSE_BUYER, u'拒绝退款'),
        (REFUND_APPROVE, u'等待返款'),
        (REFUND_CLOSED, u'退款关闭'),
        (REFUND_SUCCESS, u'退款成功'),
    )

    REFUNDABLE_STATUS = (REFUND_WAIT_SELLER_AGREE,
                         REFUND_WAIT_RETURN_GOODS,
                         REFUND_CONFIRM_GOODS,
                         REFUND_APPROVE,
                         REFUND_SUCCESS)

    REFUND_STATUS_MAP = (
        (NO_REFUND, pcfg.NO_REFUND),
        (REFUND_WAIT_SELLER_AGREE, pcfg.REFUND_WAIT_SELLER_AGREE),
        (REFUND_WAIT_RETURN_GOODS, pcfg.REFUND_WAIT_RETURN_GOODS),
        (REFUND_CONFIRM_GOODS, pcfg.REFUND_CONFIRM_GOODS),
        (REFUND_REFUSE_BUYER, pcfg.REFUND_REFUSE_BUYER),
        (REFUND_APPROVE, pcfg.REFUND_SUCCESS),
        (REFUND_CLOSED, pcfg.REFUND_CLOSED),
        (REFUND_SUCCESS, pcfg.REFUND_SUCCESS)
    )

    BUYER_NOT_RECEIVED = 0
    BUYER_RECEIVED = 1
    BUYER_RETURNED_GOODS = 2
    SELLER_OUT_STOCK = 3

    GOOD_STATUS_CHOICES = (
        (BUYER_NOT_RECEIVED, u'买家未收到货'),
        (BUYER_RECEIVED, u'买家已收到货'),
        (BUYER_RETURNED_GOODS, u'买家已退货'),
        (SELLER_OUT_STOCK, u'卖家缺货'),
    )

    id = models.AutoField(primary_key=True, verbose_name=u'ID')  # type: int
    refund_no = models.CharField(max_length=32, unique=True, default=default_refund_no,
                                 verbose_name=u'退款编号')  # type: text_type
    trade_id = models.IntegerField(verbose_name=u'交易ID')  # type: int
    order_id = models.IntegerField(verbose_name=u'订单ID')  # type: int

    buyer_id = models.BigIntegerField(db_index=True, default=0, verbose_name=u"客户ID")  # type: int
    buyer_nick = models.CharField(max_length=64, blank=True, verbose_name=u'买家昵称')  # type: Optional[text_type]
    mobile = models.CharField(max_length=20, db_index=True, blank=True, verbose_name=u'手机')  # type: Optional[text_type]
    phone = models.CharField(max_length=20, blank=True, verbose_name=u'固话')  # type: Optional[text_type]

    refund_id = models.CharField(max_length=28, blank=True, db_index=True,
                                 verbose_name=u'P++退款编号')  # type: Optional[text_type]
    charge = models.CharField(max_length=28, blank=True, db_index=True,
                              verbose_name=u'P++支付编号')  # type: Optional[text_type]
    channel = models.CharField(max_length=16, db_index=True, blank=True, choices=constants.CHANNEL_CHOICES,
                               verbose_name=u'付款方式')  # type: Optional[text_type]

    refund_channel = models.CharField(max_length=16, db_index=True, choices=constants.CHANNEL_CHOICES, blank=True,
                                      verbose_name=u'退款方式')  # type: text_type
    item_id = models.BigIntegerField(null=True, default=0, verbose_name=u'商品ID')  # type: int
    title = models.CharField(max_length=64, blank=True, verbose_name=u'出售标题')  # type: Optional[text_type]
    sku_id = models.BigIntegerField(null=True, default=0, verbose_name=u'规格ID')  # type: int
    sku_name = models.CharField(max_length=64, blank=True, verbose_name=u'规格标题')  # type: Optional[text_type]
    ware_by = models.IntegerField(db_index=True, default=0, verbose_name=u'退回仓库')  # type: int

    refund_num = models.IntegerField(default=0, verbose_name=u'退货数量')  # type: int
    total_fee = models.FloatField(default=0.0, verbose_name=u'总费用')  # type: float
    payment = models.FloatField(default=0.0, verbose_name=u'实付')  # type: float
    refund_fee = models.FloatField(default=0.0, verbose_name=u'退款费用')  # type: float
    amount_flow = JSONCharMyField(max_length=512, blank=True, default=u'{"desc":""}',
                                  verbose_name=u'退款去向')  # type: Optional[text_type]
    success_time = models.DateTimeField(db_index=True, blank=True, null=True,
                                        verbose_name=u'退款成功时间')  # type:datetime.datetime

    company_name = models.CharField(max_length=64, blank=True, verbose_name=u'退回快递公司')  # type: Optional[text_type]
    sid = models.CharField(max_length=64, db_index=True, blank=True,
                           verbose_name=u'退回快递单号')  # type: Optional[text_type]

    reason = models.TextField(max_length=200, blank=True, verbose_name=u'退款原因')  # type: Optional[text_type]
    proof_pic = JSONCharMyField(max_length=10240, default=[],
                                blank=True, null=True, verbose_name=u'佐证图片')  # type: Optional[text_type]
    desc = models.TextField(max_length=1000, blank=True, verbose_name=u'描述')  # type: Optional[text_type]
    feedback = models.TextField(max_length=1000, blank=True, verbose_name=u'审核意见')  # type: Optional[text_type]

    has_good_return = models.BooleanField(default=False, verbose_name=u'有退货')  # type: bool
    has_good_change = models.BooleanField(default=False, verbose_name=u'有换货')  # type: bool
    is_lackrefund = models.BooleanField(default=False, db_index=True, verbose_name=u'缺货自动退款')  # type: bool
    lackorder_id = models.IntegerField(null=True, db_index=True, verbose_name=u'缺货单ID')  # type: int

    good_status = models.IntegerField(db_index=True, choices=GOOD_STATUS_CHOICES, default=BUYER_RECEIVED, blank=True,
                                      verbose_name=u'退货商品状态')  # type: int
    status = models.IntegerField(db_index=True, choices=REFUND_STATUS, default=REFUND_WAIT_SELLER_AGREE, blank=True,
                                 verbose_name=u'退款状态')  # type: int
    postage_num = models.IntegerField(default=0, verbose_name=u'退邮费金额(分)')  # type: float
    coupon_num = models.IntegerField(default=0, verbose_name=u'优惠券金额(分)')  # type: float

    class Meta:
        db_table = 'flashsale_refund'
        unique_together = ("trade_id", "order_id")
        app_label = 'pay'
        verbose_name = u'特卖/退款单'
        verbose_name_plural = u'特卖/退款单列表'
        permissions = [("sale_refund_manage", u"特卖订单退款管理"), ]

    def __unicode__(self):
        # type: () -> text_type
        return '<%s>' % self.id

    @property
    def customer(self):
        # type: () -> Customer
        """ 退款用户 """
        from flashsale.pay.models import Customer

        customer = Customer.objects.get(id=self.buyer_id)
        return customer

    @property
    def sale_trade(self):
        # type: () -> SaleTrade
        from .trade import SaleTrade

        if not hasattr(self, '__sale_trade__'):
            self.__sale_trade__ = SaleTrade.objects.filter(id=self.trade_id).first()
        return self.__sale_trade__

    @property
    def saleorder(self):
        # type: () -> SaleOrder
        from .trade import SaleOrder

        if not hasattr(self, '_sale_order_'):
            self._sale_order_ = SaleOrder.objects.filter(id=self.order_id).first()
        return self._sale_order_

    @property
    def refundproduct(self):
        # type: () -> RefundProduct
        if not hasattr(self, '_refund_product_'):
            from shopback.refunds.models import RefundProduct

            self._refund_product_ = RefundProduct.objects.filter(trade_id=self.sale_trade.tid,
                                                                 sku_id=self.sku_id).first()
        return self._refund_product_

    @property
    def package_skuitem(self):
        # type: () -> PackageSkuItem
        """包裹单
        """
        if not hasattr(self, '_package_sku_item_'):
            from shopback.trades.models import PackageSkuItem

            sale_order = self.saleorder
            self._package_sku_item_ = PackageSkuItem.objects.filter(oid=sale_order.oid).first()
        return self._package_sku_item_

    @property
    def is_fastrefund(self):
        # type: () -> bool
        """　是否极速退款 """
        return True  # 所有退款都是钱包退款
        # from flashsale.pay.models import SaleTrade
        # # 钱包支付 含钱包支付　＋　支付宝支付
        # return self.refund_channel == constants.BUDGET or \
        # self.sale_trade.is_budget_paid() or \
        # self.sale_trade.channel in (SaleTrade.ALIPAY, SaleTrade.ALIPAY_WAP)

    @property
    def is_postrefund(self):
        # type: () -> int
        """　发货后退款 """
        return self.good_status in (self.BUYER_RECEIVED, self.BUYER_RETURNED_GOODS)

    @property
    def is_refundapproved(self):
        # type: () -> bool
        """　是否已同意退款 """
        return self.status in (self.REFUND_APPROVE, self.REFUND_SUCCESS)

    @property
    def is_returngoodsable(self):
        # type: () -> bool
        """ 是否可以退货: 退款单在申请状态 并且 用户已经收到包裹 """
        return self.status == SaleRefund.REFUND_WAIT_SELLER_AGREE and self.good_status == SaleRefund.BUYER_RECEIVED

    @property
    def is_modifiable(self):
        # type: () -> bool
        return self.status not in [SaleRefund.NO_REFUND,
                                   SaleRefund.REFUND_SUCCESS,
                                   SaleRefund.REFUND_CLOSED]

    def get_postage_num_display(self):
        # type: () -> float
        return self.postage_num / 100.0

    def get_coupon_num_display(self):
        # type: () -> float
        return self.coupon_num / 100.0

    def get_tid(self):
        # type: () -> text_type
        strade = self.sale_trade
        return strade.tid

    def get_oid(self):
        # type: () -> text_type
        return self.saleorder.oid

    def get_refund_desc(self):
        # type: () -> text_type
        return u'退款(oid:%s),%s' % (self.order_id, self.reason)

    def get_refund_coupons(self):
        # type: () -> Optional[List[BudgetLog]]
        from flashsale.coupon.models import UserCoupon

        return UserCoupon.objects.filter(coupon_type=UserCoupon.TYPE_COMPENSATE,
                                         customer_id=self.buyer_id,
                                         uniq_id__contains=self.trade_id)

    def get_refund_postage_budget_logs(self):
        # type: () -> List[BudgetLog]
        """
        功能：　获取补邮费退到余额信息
        """
        from flashsale.pay.models import BudgetLog

        return BudgetLog.objects.filter(referal_id=self.id, budget_log_type=BudgetLog.BG_REFUND_POSTAGE)

    def get_refund_budget_logs(self):
        # type: () -> List[BudgetLog]
        """
        功能：　获取退到余额信息
        """
        from flashsale.pay.models import BudgetLog

        return BudgetLog.objects.filter(referal_id=self.id, budget_log_type=BudgetLog.BG_REFUND)

    @classmethod
    def create_salerefund(cls, saleorder, refund_num, refund_fee, reason, good_status=None,
                          desc='', refund_channel=None, proof_pic=None):
        # type: (SaleOrder, int, float, int, text_type, text_type, Any, Any) -> SaleRefund
        """创建退款单
        """
        good_status = cls.SELLER_OUT_STOCK if good_status is None else good_status
        # 有退货字段在退货商品状态为　买家收到　买家已经退货　　时候为true
        has_good_return = True if good_status in (cls.BUYER_RECEIVED, cls.BUYER_RETURNED_GOODS) else False
        salerefund = SaleRefund(trade_id=saleorder.sale_trade.id,
                                order_id=saleorder.id,
                                buyer_id=saleorder.buyer_id,
                                item_id=saleorder.item_id,
                                charge=saleorder.sale_trade.charge,
                                channel=saleorder.sale_trade.channel,
                                sku_id=saleorder.sku_id,
                                sku_name=saleorder.sku_name,
                                refund_num=refund_num,
                                buyer_nick=saleorder.sale_trade.buyer_nick,
                                mobile=saleorder.sale_trade.receiver_mobile,
                                phone=saleorder.sale_trade.receiver_mobile,
                                total_fee=saleorder.total_fee,
                                payment=saleorder.payment,
                                refund_fee=refund_fee,
                                good_status=good_status,
                                has_good_return=has_good_return,
                                reason=reason,
                                desc=desc,
                                refund_channel=refund_channel,
                                proof_pic=proof_pic,
                                title=saleorder.title)
        salerefund.save()
        return salerefund

    @transaction.atomic
    def refund_fast_approve(self):
        # type: () -> None
        """　极速退款审核确认 """
        from .user import BudgetLog

        sorder = self.saleorder
        payment = round(self.refund_fee * 100, 0)
        blog = BudgetLog.objects.filter(customer_id=self.buyer_id,
                                        referal_id=self.id,  # 以退款单
                                        budget_log_type=BudgetLog.BG_REFUND).first()
        if blog:
            total_refund = blog.flow_amount + payment  # 总的退款金额　等于已经退的金额　加上　现在要退的金额
            if total_refund > round(sorder.payment * 100, 0):
                # 如果钱包总的退款记录数值大于子订单的实际支付额　抛出异常
                raise Exception(u'超过订单实际支付金额 !')
            else:  # 如果退款总额不大于该笔子订单的实际支付金额　则予以退款操作
                blog.flow_amount = total_refund
                blog.save(update_fields=['flow_amount'])
        else:
            if payment > round(sorder.payment * 100, 0):
                raise Exception(u'超过订单实际支付金额!')
            if payment > 0:  # 有退款金额才生成退款余额记录
                BudgetLog.create_salerefund_log(self, payment)
        self.refund_confirm()
        self.send_refund_success_weixin_message()  # 退款成功推送

    def refund_charge_approve(self):
        # type: () -> None
        ch = pingpp.Charge.retrieve(self.charge)
        re = ch.refunds.create(description=self.get_refund_desc(),
                               amount=round(self.refund_fee * 100, 0))
        self.refund_id = re.id
        self.status = SaleRefund.REFUND_APPROVE
        self.save(update_fields=['refund_id', 'status'])

    def refund_approve(self):
        # type: () -> None
        if self.is_fastrefund:
            self.refund_fast_approve()
        elif self.refund_fee > 0 and self.charge:
            self.refund_charge_approve()

    def roll_back_usercoupon(self):
        # type: () -> bool
        """退款成功返还用户使用过的优惠券（如果使用过优惠券的话）
        """
        if self.status != SaleRefund.REFUND_SUCCESS:  # 不是退款成功不处理
            return False
        from flashsale.coupon.tasks import task_roll_back_usercoupon_by_refund

        sale_trade = self.sale_trade
        refund_fees = SaleRefund.objects.filter(trade_id=self.trade_id,
                                                status=SaleRefund.REFUND_SUCCESS).values('refund_fee')
        total_refund_fee = sum([i['refund_fee'] for i in refund_fees])  # 该交易相关的退款单总退款成功费用
        if sale_trade.payment == total_refund_fee:  # 退款成功的费用和交易费用相等则退还优惠券给用户
            task_roll_back_usercoupon_by_refund.delay(sale_trade.tid, self.refund_num)
        return True

    def refund_confirm(self):
        # type: () -> None
        """ 确认退款成功，修改退款状态 """
        srefund = SaleRefund.objects.get(id=self.id)
        if srefund.status == SaleRefund.REFUND_SUCCESS:
            return
        self.success_time = datetime.datetime.now()
        self.status = SaleRefund.REFUND_SUCCESS
        self.save()
        from .trade import SaleOrder, SaleTrade

        sorder = SaleOrder.objects.get(id=self.order_id)
        sorder.refund_status = SaleRefund.REFUND_SUCCESS
        if sorder.status in (SaleTrade.WAIT_SELLER_SEND_GOODS,
                             SaleTrade.WAIT_BUYER_CONFIRM_GOODS,
                             SaleTrade.TRADE_BUYER_SIGNED):
            sorder.status = SaleTrade.TRADE_CLOSED
        sorder.save(update_fields=['status', 'modified'])

        strade = sorder.sale_trade
        if strade.normal_orders.count() == 0:
            strade.status = SaleTrade.TRADE_CLOSED
            strade.save(update_fields=['status', 'modified'])
        signal_saletrade_refund_confirm.send(sender=SaleRefund, obj=self)
        self.roll_back_usercoupon()

    def pic_path(self):
        # type: () -> text_type
        try:
            pro = Product.objects.get(id=self.item_id)
            return pro.pic_path
        except Product.DoesNotExist:
            return ''

    def sale_contactor(self):
        # type: () -> int
        """ 选品买手　"""
        try:
            pro = Product.objects.get(id=self.item_id)
            sal = SaleProduct.objects.get(id=pro.sale_product)
            return sal.contactor.id
        except:
            return 0

    def pro_model(self):
        # type: () -> int
        try:
            pro = Product.objects.get(id=self.item_id)
            return pro.model_id
        except Product.DoesNotExist:
            return 0

    def outer_id(self):
        # type: () -> text_type
        try:
            pro = Product.objects.get(id=self.item_id)
            return pro.outer_id
        except Product.DoesNotExist:
            return ''

    def get_return_address(self):
        # type: () -> text_type
        """ 退货地址 """
        if self.status < self.REFUND_WAIT_RETURN_GOODS:
            return u'退货状态未确定'
        from shopback.warehouse.models import WareHouse
        from .trade import SaleOrder
        from shopback.items.models import Product

        sorder = SaleOrder.objects.get(id=self.order_id)
        try:
            sproduct = Product.objects.filter(id=sorder.item_id).first()
            if sproduct:
                ware_by = sproduct.ware_by
                if ware_by == WARE_THIRD:
                    return_by = sproduct.get_supplier().return_ware_by
                    if return_by in [WARE_SH, WARE_GZ, WARE_COMPANY]:
                        ware_by = return_by
                return WareHouse.objects.get(id=ware_by).address
        except WareHouse.DoesNotExist:
            logger.warn('order product ware_by not found:saleorder=%s' % sorder)
        return u'退货地址请咨询小鹿美美客服哦'

    def refund_status_shaft(self):
        # type: () -> List[Dict[str, Any]]
        """状态轴"""
        if self.status in (SaleRefund.NO_REFUND, SaleRefund.REFUND_WAIT_SELLER_AGREE):
            return [{"status_display": self.get_status_display(), "time": self.modified}]
        if self.good_status in (SaleRefund.SELLER_OUT_STOCK, SaleRefund.BUYER_NOT_RECEIVED):  # 退款(没有发货)
            data = [{"status_display": u'申请退款', "time": self.created}]
            if self.status == SaleRefund.REFUND_SUCCESS:  # 退款成功
                data.append({"status_display": u'等待返款', "time": self.modified})
            data.append({"status_display": self.get_status_display(), "time": self.modified})
        else:  # 发货后退款
            data = [{"status_display": u'申请退款', "time": self.created}]
            if self.status in (SaleRefund.REFUND_CONFIRM_GOODS,  # 退货途中
                               SaleRefund.REFUND_APPROVE,  # 等待返款
                               SaleRefund.REFUND_SUCCESS):  # 退款成功
                data.append({"status_display": u'同意申请', "time": self.modified})
            data.append({"status_display": self.get_status_display(), "time": self.modified})
        return data

    def agree_return_goods(self):
        # type: () -> bool
        """ 同意退货 """
        if self.is_returngoodsable:  # 退款待审　买家已经收到货
            self.status = SaleRefund.REFUND_WAIT_RETURN_GOODS
            self.save(update_fields=['status', 'modified'])
            self.send_refund_agree_weixin_message()  # 发送同意退货申请
            return True
        return False

    def get_weixin_push_content(self, event_type):
        # type: (int) -> text_type
        """ 返回对应的　推送类型　的　推送信息内容
        """
        from flashsale.xiaolumm.models import WeixinPushEvent

        content_map = {
            WeixinPushEvent.SALE_REFUND_AGREE: u'退货申请审核通过！\n请及时填写退货 ==>物 流 单 号<== 以便系统更快处理退货!',
            WeixinPushEvent.SALE_REFUND_ARRIVE: u'仓库已收货，检验后即将完成退款。',
            WeixinPushEvent.SALE_REFUND_GOODS_SUCCESS: u'已经退款成功\n退款金额已转入小鹿零钱帐户,请及时查看.'
        }
        return content_map[event_type]

    def send_refund_agree_weixin_message(self):
        # type : () -> None
        from flashsale.xiaolumm.models import WeixinPushEvent
        from shopapp.weixin.weixin_push import WeixinPush

        push = WeixinPush()
        push.push_refund_notify(self, WeixinPushEvent.SALE_REFUND_AGREE)  # 推送同意退款微信消息

    def send_refund_success_weixin_message(self):
        # type : () -> None
        """发送退款成功微信推送
        """
        from flashsale.xiaolumm.models import WeixinPushEvent
        from shopapp.weixin.weixin_push import WeixinPush

        push = WeixinPush()
        push.push_refund_notify(self, WeixinPushEvent.SALE_REFUND_GOODS_SUCCESS)  # 推送退款成功微信消息


def handle_sale_refund_signal(sender, instance, created, raw, *args, **kwargs):
    """ 特卖退款单生成触发更新库存数及锁定数信号 """
    if raw: return
    from .trade import SaleTrade
    from shopback import signals
    from shopback.trades.models import MergeOrder

    strade = SaleTrade.objects.get(id=instance.trade_id)
    if (not strade.is_Deposite_Order() and created and
                instance.status == SaleRefund.REFUND_WAIT_SELLER_AGREE):
        signals.order_refund_signal.send(sender=MergeOrder, obj=instance)


post_save.connect(handle_sale_refund_signal, sender=SaleRefund)


def category_refund_stat(sender, obj, **kwargs):
    """
        通过信号写对应上架日期的产品分类的退款数量和金额
    """
    pro = Product.objects.get(id=obj.item_id)
    cgysta, state = CategorySaleStat.objects.get_or_create(stat_date=pro.sale_time, category=pro.category.cid)
    if state:  # 如果是新建
        cgysta.refund_num = obj.refund_num
        cgysta.refund_amount = obj.refund_fee
    else:  # 在原有基础上面加退款数量和退款金额
        cgysta.refund_num = F("refund_num") + obj.refund_num
        cgysta.refund_amount = F("refund_amount") + obj.refund_fee
    update_model_fields(cgysta, update_fields=["refund_num", "refund_amount"])


signal_saletrade_refund_post.connect(category_refund_stat, sender=SaleRefund)


def sync_sale_refund_status(sender, instance, created, **kwargs):
    # created 表示实例是否创建 （修改）
    # 允许抛出异常
    from .trade import SaleTrade, SaleOrder

    order = SaleOrder.objects.get(id=instance.order_id)
    trade = SaleTrade.objects.get(id=instance.trade_id)
    # 退款成功  如果是退款关闭要不要考虑？？？
    order_update_fields = ['modified']
    if instance.status == SaleRefund.REFUND_SUCCESS:
        # 如果是退款成功状态
        # 找到订单
        refund_num = instance.refund_num  # 退款数量
        order_num = order.num  # 订单数量
        if refund_num == order_num:  # 退款数量等于订单数量
            # 关闭这个订单
            order.status = SaleOrder.TRADE_CLOSED  # 退款关闭
            order_update_fields.append('status')
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
            order_update_fields.append('status')
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
    order_update_fields.append('refund_status')
    if not order.refund_id:
        order.refund_id = instance.id
        order.refund_fee = instance.refund_fee
        order_update_fields.extend(['refund_id', 'refund_fee'])

    order.save(update_fields=order_update_fields)  # 保存同步的状态


post_save.connect(sync_sale_refund_status, sender=SaleRefund, dispatch_uid=u'post_save_sync_sale_refund_status')
