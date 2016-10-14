# -*- coding:utf-8 -*-
import time
import datetime
from django.db import models
from django.db.models import Q, Sum
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.db.models import F

from shopback.categorys.models import CategorySaleStat
from common.modelutils import update_model_fields
from core.options import log_action, ADDITION, CHANGE, get_systemoa_user
from core.fields import JSONCharMyField

from shopback import paramconfig as pcfg
from shopback.items.models import Product
from supplychain.supplier.models import SaleProduct
from flashsale.pay.signals import signal_saletrade_refund_post
from flashsale.pay import NO_REFUND, REFUND_CLOSED, REFUND_REFUSE_BUYER, REFUND_WAIT_SELLER_AGREE, \
    REFUND_WAIT_RETURN_GOODS, REFUND_CONFIRM_GOODS, REFUND_APPROVE, REFUND_SUCCESS, REFUND_STATUS
from flashsale.pay.managers import SaleRefundManager
from shopback.warehouse.constants import WARE_THIRD, WARE_SH, WARE_GZ, WARE_COMPANY
from ..signals import signal_saletrade_refund_confirm
from ..options import uniqid
from .base import PayBaseModel
from .. import constants

import pingpp
pingpp.api_key = settings.PINGPP_APPKEY

import logging
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

    id = models.AutoField(primary_key=True, verbose_name=u'ID')
    refund_no = models.CharField(max_length=32, unique=True,
                                 default=default_refund_no,
                                 verbose_name=u'退款编号')
    trade_id = models.IntegerField(verbose_name=u'交易ID')
    order_id = models.IntegerField(verbose_name=u'订单ID')

    buyer_id = models.BigIntegerField(db_index=True, default=0, verbose_name=u"客户ID")
    refund_id = models.CharField(max_length=28, blank=True, db_index=True, verbose_name=u'P++退款编号')
    charge = models.CharField(max_length=28, blank=True, db_index=True, verbose_name=u'P++支付编号')
    channel = models.CharField(max_length=16, db_index=True,
                               choices=constants.CHANNEL_CHOICES, blank=True, verbose_name=u'付款方式')

    refund_channel = models.CharField(max_length=16, db_index=True,
                               choices=constants.CHANNEL_CHOICES, blank=True, verbose_name=u'退款方式')

    item_id = models.BigIntegerField(null=True, default=0, verbose_name=u'商品ID')
    title = models.CharField(max_length=64, blank=True, verbose_name=u'出售标题')
    ware_by = models.IntegerField(db_index=True, default=0, verbose_name=u'退回仓库')

    sku_id = models.BigIntegerField(null=True, default=0, verbose_name=u'规格ID')
    sku_name = models.CharField(max_length=64, blank=True, verbose_name=u'规格标题')
    refund_num = models.IntegerField(default=0, verbose_name=u'退货数量')

    buyer_nick = models.CharField(max_length=64, blank=True, verbose_name=u'买家昵称')
    mobile = models.CharField(max_length=20, db_index=True, blank=True, verbose_name=u'手机')
    phone = models.CharField(max_length=20, blank=True, verbose_name=u'固话')

    total_fee   = models.FloatField(default=0.0, verbose_name=u'总费用')
    payment     = models.FloatField(default=0.0, verbose_name=u'实付')
    refund_fee  = models.FloatField(default=0.0, verbose_name=u'退款费用')
    amount_flow = JSONCharMyField(max_length=512, blank=True, default=u'{"desc":""}', verbose_name=u'退款去向')
    success_time = models.DateTimeField(db_index=True, blank=True, null=True, verbose_name=u'退款成功时间')

    company_name = models.CharField(max_length=64, blank=True, verbose_name=u'退回快递公司')
    sid = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'退回快递单号')

    reason = models.TextField(max_length=200, blank=True, verbose_name=u'退款原因')
    proof_pic = JSONCharMyField(max_length=10240, default=[],
                                blank=True, null=True, verbose_name=u'佐证图片')
    desc = models.TextField(max_length=1000, blank=True, verbose_name=u'描述')
    feedback = models.TextField(max_length=1000, blank=True, verbose_name=u'审核意见')

    has_good_return = models.BooleanField(default=False, verbose_name=u'有退货')
    has_good_change = models.BooleanField(default=False, verbose_name=u'有换货')
    is_lackrefund   = models.BooleanField(default=False, db_index=True, verbose_name=u'缺货自动退款')
    lackorder_id    = models.IntegerField(null=True, db_index=True, verbose_name=u'缺货单ID')

    good_status = models.IntegerField(
        db_index=True, choices=GOOD_STATUS_CHOICES,
        default=BUYER_RECEIVED, blank=True, verbose_name=u'退货商品状态'
    )
    status = models.IntegerField(
        db_index=True, choices=REFUND_STATUS,
        default=REFUND_WAIT_SELLER_AGREE, blank=True, verbose_name=u'退款状态'
    )
    postage_num = models.IntegerField(default=0, verbose_name=u'退邮费金额(分)')
    coupon_num = models.IntegerField(default=0, verbose_name=u'优惠券金额(分)')

    objects = SaleRefundManager()

    class Meta:
        db_table = 'flashsale_refund'
        unique_together = ("trade_id", "order_id")
        app_label = 'pay'
        verbose_name = u'特卖/退款单'
        verbose_name_plural = u'特卖/退款单列表'
        permissions = [("sale_refund_manage", u"特卖订单退款管理"), ]

    def __unicode__(self):
        return '<%s>' % (self.id)

    def refund_desc(self):
        return u'退款(oid:%s),%s' % (self.order_id, self.reason)

    def is_fastrefund(self):
        """　是否极速退款 """
        from flashsale.pay.models import SaleTrade

        return self.refund_channel == constants.BUDGET or \
               self.sale_trade.is_budget_paid() or \
               self.sale_trade.channel in (SaleTrade.ALIPAY, SaleTrade.ALIPAY_WAP)

    def is_postrefund(self):
        """　发货后退款 """
        return self.good_status in (self.BUYER_RECEIVED, self.BUYER_RETURNED_GOODS)

    @property
    def sale_trade(self):
        from .trade import SaleTrade
        if not hasattr(self, '__sale_trade__'):
            self.__sale_trade__ = SaleTrade.objects.filter(id=self.trade_id).first()
        return self.__sale_trade__

    def sale_order(self):
        from .trade import SaleOrder
        if not hasattr(self, '_sale_order_'):
            self._sale_order_ = SaleOrder.objects.filter(id=self.order_id).first()
        return self._sale_order_

    @property
    def refundproduct(self):
        if not hasattr(self, '_refund_product_'):
            from shopback.refunds.models import RefundProduct
            self._refund_product_ = RefundProduct.objects.filter(trade_id=self.sale_trade.tid,
                                                                 sku_id=self.sku_id).first()
        return self._refund_product_

    @property
    def package_skuitem(self):
        """包裹单
        """
        if not hasattr(self, '_package_sku_item_'):
            from shopback.trades.models import PackageSkuItem
            sale_order = self.sale_order()
            self._package_sku_item_ = PackageSkuItem.objects.filter(oid=sale_order.oid).first()
        return self._package_sku_item_

    def get_tid(self):
        strade = self.sale_trade
        return strade.tid

    def get_oid(self):
        sorder = self.sale_order()
        return sorder.oid

    def get_refund_budget_logs(self):
        """
        功能：　获取退到余额信息
        """
        from flashsale.pay.models import BudgetLog
        return BudgetLog.objects.filter(referal_id=self.id, budget_log_type=BudgetLog.BG_REFUND)

    @property
    def is_refundapproved(self):
        """　是否已同意退款 """
        return self.status in (self.REFUND_APPROVE, self.REFUND_SUCCESS)

    @transaction.atomic
    def refund_wallet_approve(self):
        """ deprecated 退款至妈妈钱包 """
        from .user import Customer
        from flashsale.xiaolumm.models import XiaoluMama, CarryLog


        strade = self.sale_trade
        sorder = self.sale_order
        customer = Customer.objects.normal_customer.filter(id=strade.buyer_id).first()

        payment = round(self.refund_fee * 100, 0)
        xlmm  = XiaoluMama.objects.filter(openid=customer.unionid).first()
        if not xlmm:
            raise Exception(u'妈妈unoind:%s' % customer.unionid)

        clog = CarryLog.objects.filter(xlmm=xlmm.id,
                                       order_num=self.order_id,  # 以子订单为准
                                       log_type=CarryLog.REFUND_RETURN).first()
        if clog:
            total_refund = clog.value + payment  # 总的退款金额　等于已经退的金额　加上　现在要退的金额
            if total_refund > round(sorder.payment * 100, 0):
                # 如果钱包总的退款记录数值大于子订单的实际支付额　抛出异常
                raise Exception(u'超过订单实际支付金额!')
            else:
                # 如果退款总额不大于该笔子订单的实际支付金额　则予以退款操作
                clog.value = total_refund
                clog.save()
                # 操作记录
                xlmm.cash=models.F('cash') + payment
                xlmm.save(update_fields=['cash'])
                log_action(get_systemoa_user(), self, CHANGE, u'二次退款审核通过:%s' % self.refund_id)
        # assert clogs.count() == 0, u'订单已经退款！'
        else:  # 钱包中不存在该笔子订单的历史退款记录　则创建记录
            if payment > round(sorder.payment * 100, 0):
                raise Exception(u'超过订单实际支付金额!')
            CarryLog.objects.create(xlmm=xlmm.id,
                                    order_num=self.order_id,
                                    buyer_nick=strade.buyer_nick,
                                    value=payment,
                                    log_type=CarryLog.REFUND_RETURN,
                                    carry_type=CarryLog.CARRY_IN,
                                    status=CarryLog.CONFIRMED)
            xlmm.cash = models.F('cash') + payment
            xlmm.save(update_fields=['cash'])
        self.refund_confirm()

    @transaction.atomic
    def refund_fast_approve(self):
        """　极速退款审核确认 """
        from .user import BudgetLog
        strade = self.sale_trade
        sorder = self.sale_order()

        obj = self
        payment = round(obj.refund_fee * 100, 0)
        blog = BudgetLog.objects.filter(customer_id=strade.buyer_id,
                                         referal_id=obj.order_id,  # 以子订单为准
                                         budget_log_type=BudgetLog.BG_REFUND).first()
        if blog:
            total_refund = blog.flow_amount + payment  # 总的退款金额　等于已经退的金额　加上　现在要退的金额
            if total_refund > round(sorder.payment * 100, 0):
                # 如果钱包总的退款记录数值大于子订单的实际支付额　抛出异常
                raise Exception(u'超过订单实际支付金额!')
            else:  # 如果退款总额不大于该笔子订单的实际支付金额　则予以退款操作
                blog.flow_amount = total_refund
                blog.save(update_fields=['flow_amount'])
        else:
            if payment > round(sorder.payment * 100, 0):
                raise Exception(u'超过订单实际支付金额!')
            BudgetLog.objects.create(
                customer_id=strade.buyer_id,
                referal_id=obj.order_id,
                flow_amount=payment,
                budget_type=BudgetLog.BUDGET_IN,
                budget_log_type=BudgetLog.BG_REFUND,
                status=BudgetLog.CONFIRMED
            )
        self.refund_confirm()

    def refund_charge_approve(self):
        ch = pingpp.Charge.retrieve(self.charge)
        re = ch.refunds.create(description=self.refund_desc(),
                               amount=round(self.refund_fee * 100, 0))
        self.refund_id = re.id
        self.status = SaleRefund.REFUND_APPROVE
        self.save(update_fields=['refund_id', 'status'])

    def refund_approve(self):

        from .trade import SaleTrade
        strade = self.sale_trade
        if strade.channel == SaleTrade.WALLET:
            self.refund_wallet_approve()

        elif self.is_fastrefund():
            self.refund_fast_approve()

        elif self.refund_fee > 0 and self.charge:
            self.refund_charge_approve()

    def refund_confirm(self):
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
        if sorder.status in (
                SaleTrade.WAIT_SELLER_SEND_GOODS,
                SaleTrade.WAIT_BUYER_CONFIRM_GOODS,
                SaleTrade.TRADE_BUYER_SIGNED):
            sorder.status = SaleTrade.TRADE_CLOSED
        sorder.save()

        strade = sorder.sale_trade
        if strade.normal_orders.count() == 0:
            strade.status = SaleTrade.TRADE_CLOSED
            strade.save()
        signal_saletrade_refund_confirm.send(sender=SaleRefund, obj=self)

    def pic_path(self):
        try:
            pro = Product.objects.get(id=self.item_id)
            return pro.pic_path
        except Product.DoesNotExist:
            return None

    def sale_contactor(self):
        """ 选品买手　"""
        try:
            pro = Product.objects.get(id=self.item_id)
            sal = SaleProduct.objects.get(id=pro.sale_product)
            return sal.contactor.id
        except:
            return None

    def pro_model(self):
        try:
            pro = Product.objects.get(id=self.item_id)
            return pro.model_id
        except Product.DoesNotExist:
            return None

    def outer_id(self):
        try:
            pro = Product.objects.get(id=self.item_id)
            return pro.outer_id
        except Product.DoesNotExist:
            return None

    def get_return_address(self):
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

    def get_refund_customer(self):
        """ 退款用户 """
        from flashsale.pay.models import Customer
        customer = Customer.objects.get(id=self.buyer_id)
        return customer

    def refund_status_shaft(self):
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

    def update_sale_order_refund_status(self):
        """ 更新订单的退款状态等于退款单的状态 """
        sale_order = self.sale_order()
        sale_order.refund_status = self.status
        sale_order.save(update_fields=['refund_status', 'modified'])
        return

    def agree_return_goods(self):
        """ 同意退货 """
        if self.is_returngoodsable:
            self.status = SaleRefund.REFUND_WAIT_RETURN_GOODS
            self.save(update_fields=['status', 'modified'])
            return True
        return False

    @property
    def postage_num_display(self):
        return self.postage_num / 100.0

    @property
    def coupon_num_display(self):
        return self.coupon_num / 100.0

    @property
    def is_returngoodsable(self):
        """ 是否可以退货: 退款单在申请状态 并且 用户已经收到包裹 """
        return self.status == SaleRefund.REFUND_WAIT_SELLER_AGREE and self.good_status == SaleRefund.BUYER_RECEIVED

    @property
    def is_modifiable(self):
        return self.status not in [SaleRefund.NO_REFUND,
                                   SaleRefund.REFUND_SUCCESS,
                                   SaleRefund.REFUND_CLOSED]

    @property
    def is_seller_responsible(self):
        """
        功能：　判断　退款原因　是否是　商家责任
        """
        from shopback.refunds.models import REFUND_REASON
        # 商家责任
        if self.reason in [REFUND_REASON[2][1],  # 缺货
                           REFUND_REASON[3][1],  # 开线
                           REFUND_REASON[4][1],  # 发错货
                           REFUND_REASON[5][1],  # 没有发货
                           REFUND_REASON[6][1],  # 未收到货
                           REFUND_REASON[7][1],  # 与描述不符
                           REFUND_REASON[8][1],  # 退运费
                           REFUND_REASON[9][1]]:  # 发票问题
            return True
        return False

    def get_weixin_push_content(self, event_type):
        """ 返回对应的　推送类型　的　推送信息内容
        """
        from flashsale.xiaolumm.models import WeixinPushEvent

        postage_coupon_info = u'附加信息:'
        if (self.coupon_num + self.postage_num) == 0:
            postage_coupon_info = u''
        else:
            if self.postage_num > 0:
                postage_coupon_info += u'补邮费:￥%s' % self.postage_num / 100.0
            if self.coupon_num > 0:
                postage_coupon_info += u'现金券:￥%s' % self.coupon_num / 100.0
        content_map = {
            WeixinPushEvent.SALE_REFUND_AGREE: u'公主殿下，你的退货申请已经审核通过！请及时填写退货＊物流单号＊，以便系统跟踪你的退货进度!',
            WeixinPushEvent.SALE_REFUND_ARRIVE: u'仓库已收货，检验后即将完成退款。',
            WeixinPushEvent.SALE_REFUND_GOODS_SUCCESS: u'已经退款成功。退款金额已经转入你的小鹿零钱帐户，请及时查看。%s' % postage_coupon_info
        }
        return content_map[event_type]

    def send_return_goods_back_message(self):
        """
        功能：　同意退货　后　发送　消息给用户　让用户　填写物流信息和快递单号
        """
        from shopapp.weixin.weixin_push import WeixinPush
        from flashsale.xiaolumm.models import WeixinPushEvent

        push = WeixinPush()
        push.push_refund_notify(self, WeixinPushEvent.SALE_REFUND_AGREE)

    def auto_approve_return_goods(self):
        """
        自动同意退货:
        1. 用户提交退款单　
        如果是退货申请　则　修改该退款单状态到　同意申请状态
        """
        # if not self.is_seller_responsible:  # 非商家原因造成的退货
        self.agree_return_goods()
        self.send_return_goods_back_message()
        return True
        # return False

    @transaction.atomic()
    def return_fee_by_refund_product(self):
        """
        功能：　根据　refund app 的RefundProduct 来给用户退款
        1. 状态检查
        2. 退　退款　到余额
        3. 退　邮费　到余额
        4. 补贴　优惠券
        5. 修改退款单状态
        """
        if self.good_status != SaleRefund.BUYER_RETURNED_GOODS or self.status != SaleRefund.REFUND_CONFIRM_GOODS:
            return logger.error({'action': u'return_fee_by_refund_product',
                                 'message': u'退款单状态错误 不予退款',
                                 'salerefund': self.id})
        from flashsale.pay.models import BudgetLog
        from flashsale.coupon.models import UserCoupon
        from shopapp.weixin.weixin_push import WeixinPush
        from flashsale.xiaolumm.models import WeixinPushEvent

        flow_amount = min(self.refund_fee, self.payment)*100
        BudgetLog.create_salerefund_log(self, flow_amount)
        if 0 < self.postage_num <= 2000:
            BudgetLog.create_salerefund_log(self, self.postage_num)
        if self.coupon_num > 0:
            UserCoupon.create_salerefund_post_coupon(self.buyer_id, self.trade_id, money=(self.coupon_num / 100))
        self.status = SaleRefund.REFUND_SUCCESS
        self.save(update_fields=['status'])

        push = WeixinPush()
        push.push_refund_notify(self, WeixinPushEvent.SALE_REFUND_GOODS_SUCCESS)
        return True


def roll_back_usercoupon_status(sender, instance, created, *args, **kwargs):
    """
     当一笔交易的所有sale_order 都退款成功了　则　退回被使用的优惠券
    """
    if instance.status != SaleRefund.REFUND_SUCCESS:  # 不是退款成功不处理
        return
    from flashsale.coupon.tasks import task_roll_back_usercoupon_by_refund

    sale_trade = instance.sale_trade
    sale_orders = sale_trade.sale_orders.all()
    refunds = SaleRefund.objects.filter(trade_id=instance.trade_id)
    if refunds.count() < sale_orders.count():  # 保证map是所有的sale_order的退款单
        return
    refunds_status = refunds.values('status')
    r = map(lambda x: x['status'] == SaleRefund.REFUND_SUCCESS, refunds_status)
    if False in r:  # 有没有退款成功的订单（不退优惠券）
        return
    task_roll_back_usercoupon_by_refund.delay(sale_trade.tid)


post_save.connect(roll_back_usercoupon_status, sender=SaleRefund, dispatch_uid='post_save_roll_back_usercoupon_status')


def buyeridPatch():
    from .trade import SaleTrade
    sfs = SaleRefund.objects.all()
    for sf in sfs:
        st = SaleTrade.objects.get(id=sf.trade_id)
        sf.buyer_id = st.buyer_id
        sf.save()


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