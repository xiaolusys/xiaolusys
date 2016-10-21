# -*- coding:utf8 -*-
__author__ = 'meixqhi'
import json
import time
import datetime
from common.utils import parse_datetime
from django.db import models
from django.utils.functional import cached_property
from django.db.models import Sum
from shopback import paramconfig as pcfg
from shopback.users.models import User
from django.db.models.signals import post_save
from auth import apis
import logging
from models_refund_rate import PayRefundRate, PayRefNumRcord
from signals_refund_rate import triger_refund_record

logger = logging.getLogger('django.request')

REFUND_STATUS = (
    (pcfg.NO_REFUND, '没有退款'),
    (pcfg.REFUND_WAIT_SELLER_AGREE, '买家已经申请退款'),
    (pcfg.REFUND_WAIT_RETURN_GOODS, '卖家已经同意退款'),
    (pcfg.REFUND_CONFIRM_GOODS, '买家已经退货'),
    (pcfg.REFUND_REFUSE_BUYER, '卖家拒绝退款'),
    (pcfg.REFUND_CLOSED, '退款关闭'),
    (pcfg.REFUND_SUCCESS, '退款成功'),
)

GOOD_STATUS_CHOICES = (
    ('BUYER_NOT_RECEIVED', '买家未收到货'),
    ('BUYER_RECEIVED', '买家已收到货'),
    ('BUYER_RETURNED_GOODS', '买家已退货'),
)

ORDER_STATUS_CHOICES = (
    (pcfg.TRADE_NO_CREATE_PAY, '没有创建支付宝交易'),
    (pcfg.WAIT_BUYER_PAY, '等待买家付款'),
    (pcfg.WAIT_SELLER_SEND_GOODS, '等待卖家发货'),
    (pcfg.WAIT_BUYER_CONFIRM_GOODS, '等待买家确认收货'),
    (pcfg.TRADE_BUYER_SIGNED, '已签收,货到付款专用'),
    (pcfg.TRADE_FINISHED, '交易成功'),
    (pcfg.TRADE_CLOSED, '退款成功交易自动关闭'),
    (pcfg.TRADE_CLOSED_BY_TAOBAO, '付款前关闭交易'),
)

# 不需客服介入1; 需要客服介入2; 客服已经介入3; 客服初审完成 4; 客服主管复审失败5; 客服处理完成6;
CS_STATUS_CHOICES = (
    (1, '不需客服介入'),
    (2, '需要客服介入'),
    (3, '客服已经介入'),
    (4, '客服初审完成'),
    (5, '客服主管复审失败'),
    (6, '客服处理完成'),
)
REFUND_REASON = (
    (0, u'其他'),
    (1, u'错拍'),
    (2, u'缺货'),
    (3, u'开线/脱色/脱毛/有色差/有虫洞'),
    (4, u'发错货/漏发'),
    (5, u'没有发货'),
    (6, u'未收到货'),
    (7, u'与描述不符'),
    (8, u'退运费'),
    (9, u'发票问题'),
    (10, u'七天无理由退换货')
)
def default_refund_no():
    return int(time.time() * 10 ** 4)

def default_refund_id():
    return 'RF%d' % int(time.time() * 10 ** 4)

class Refund(models.Model):
    NO_REFUND = pcfg.NO_REFUND
    REFUND_WAIT_SELLER_AGREE = pcfg.REFUND_WAIT_SELLER_AGREE
    REFUND_WAIT_RETURN_GOODS = pcfg.REFUND_WAIT_RETURN_GOODS
    REFUND_CONFIRM_GOODS = pcfg.REFUND_CONFIRM_GOODS
    REFUND_REFUSE_BUYER = pcfg.REFUND_REFUSE_BUYER
    REFUND_CLOSED = pcfg.REFUND_CLOSED
    REFUND_SUCCESS = pcfg.REFUND_SUCCESS

    id = models.BigIntegerField(primary_key=True, default=default_refund_no, verbose_name='ID')
    refund_id = models.CharField(max_length=32,
                                 default=default_refund_id,
                                 verbose_name='退款单ID')
    tid = models.CharField(max_length=32, blank=True, verbose_name='交易ID')

    title = models.CharField(max_length=64, blank=True, verbose_name='出售标题')
    num_iid = models.BigIntegerField(null=True, default=0, verbose_name='商品ID')

    user = models.ForeignKey(User, null=True, related_name='refunds', verbose_name='店铺')
    seller_id = models.CharField(max_length=64, blank=True, verbose_name='卖家ID')
    buyer_nick = models.CharField(max_length=64, db_index=True, blank=True, verbose_name='买家昵称')
    seller_nick = models.CharField(max_length=64, blank=True, verbose_name='卖家昵称')

    mobile = models.CharField(max_length=20, db_index=True, blank=True, verbose_name='手机')
    phone = models.CharField(max_length=20, db_index=True, blank=True, verbose_name='固话')

    total_fee = models.CharField(max_length=10, blank=True, verbose_name='总费用')
    refund_fee = models.CharField(max_length=10, blank=True, verbose_name='退款费用')
    payment = models.CharField(max_length=10, blank=True, verbose_name='实付')

    created = models.DateTimeField(db_index=True, null=True, auto_now_add=True, verbose_name='创建日期')
    modified = models.DateTimeField(db_index=True, null=True, auto_now=True, verbose_name='修改日期')

    oid = models.CharField(db_index=True, max_length=32, blank=True, verbose_name='订单ID')
    company_name = models.CharField(max_length=64, blank=True, verbose_name='快递公司')
    sid = models.CharField(max_length=64, db_index=True, blank=True, verbose_name='快递单号')

    reason = models.TextField(max_length=200, blank=True, verbose_name='退款原因')
    desc = models.TextField(max_length=1000, blank=True, verbose_name='描述')
    has_good_return = models.BooleanField(default=False, verbose_name='是否退货')

    is_reissue = models.BooleanField(default=False, verbose_name='已处理')

    good_status = models.CharField(max_length=32, blank=True,
                                   choices=GOOD_STATUS_CHOICES, verbose_name='退货商品状态')
    order_status = models.CharField(max_length=32, blank=True,
                                    choices=ORDER_STATUS_CHOICES, verbose_name='订单状态')
    cs_status = models.IntegerField(default=1,
                                    choices=CS_STATUS_CHOICES, verbose_name='客服介入状态')
    status = models.CharField(max_length=32, blank=True,
                              choices=REFUND_STATUS, verbose_name='退款状态')

    class Meta:
        db_table = 'shop_refunds_refund'
        unique_together = ("refund_id", "tid")
        app_label = 'refunds'
        verbose_name = u'退货款单'
        verbose_name_plural = u'退货款单列表'

    def __unicode__(self):
        return '<%s,%s,%s>' % (self.tid, self.buyer_nick, self.refund_fee)

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                setattr(self, field.name, getattr(self, field.name).strip())

    @classmethod
    def get_or_create(cls, user_id, refund_id, force_update=False):
        refund, state = cls.objects.get_or_create(refund_id=refund_id)
        if state or force_update:
            try:
                response = apis.taobao_refund_get(refund_id, tb_user_id=user_id)
                refund_dict = response['refund_get_response']['refund']
                refund.save_refund_through_dict(user_id, refund_dict)
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
        return refund

    def save_refund_through_dict(self, seller_id, refund):

        self.user = User.objects.get(visitor_id=seller_id)
        from shopback.trades.models import MergeTrade
        try:
            merge_trade = MergeTrade.objects.get(tid=refund['tid'])
        except:
            merge_trade = None

        self.mobile = merge_trade and merge_trade.receiver_mobile or ''
        self.phone = merge_trade and merge_trade.receiver_phone or ''

        for k, v in refund.iteritems():
            hasattr(self, k) and setattr(self, k, v)

        self.created = parse_datetime(refund['created']) \
            if refund.get('created', None) else None
        self.modified = parse_datetime(refund['modified']) \
            if refund.get('modified', None) else None

        self.save()

    def confirm_refund(self):

        from shopback.trades.models import MergeTrade, MergeOrder
        # 更新订单明细退款状态
        self_oid = self.oid
        if not self_oid:
            self_oid = self.tid
            mos = MergeOrder.objects.filter(oid=self.oid, merge_trade__tid=self.tid)
            if mos.count() == 0:
                moos = MergeOrder.objects.filter(merge_trade__tid=self.tid)
                if moos.count() == 1:
                    self_oid = moos[0].oid

        mos = MergeOrder.objects.filter(oid=self_oid)
        if mos.count() == 0:
            raise Exception('unexpect order no:%s-%s' % (self.tid, self_oid))

        mos.update(refund_status=pcfg.REFUND_SUCCESS)

        # 判断订单是否所有商品都已退款
        for o in mos:
            t = o.merge_trade
            if t.user != self.user:
                self.user = t.user

            order_qs = t.normal_orders.filter(refund_status__in=(pcfg.NO_REFUND, pcfg.REFUND_CLOSED))
            if order_qs.count() == 0:
                t.status = pcfg.TRADE_CLOSED

            t.save()


# 如果创建的退货单有退款编号，就要删除系统没有退款编号的交易
def save_refund_and_remove_unrefunded(sender, instance, *args, **kwargs):
    if instance.refund_id and not instance.is_reissue:
        refunds = Refund.objects.filter(tid=instance.tid, refund_id=None)
        if refunds.filter(is_reissue=True):
            instance.is_reissue = True
            instance.save()
        else:
            refunds.delete()


post_save.connect(save_refund_and_remove_unrefunded, sender=Refund, dispatch_uid="id_remove_unrefunded")


class RefundProduct(models.Model):
    buyer_nick = models.CharField(max_length=64, db_index=True, blank=True, verbose_name='买家昵称')
    buyer_mobile = models.CharField(max_length=22, db_index=True, blank=True, verbose_name='手机')
    buyer_phone = models.CharField(max_length=22, db_index=True, blank=True, verbose_name='固话')
    trade_id = models.CharField(max_length=64, db_index=True, blank=True, default='', verbose_name='原单ID')
    out_sid = models.CharField(max_length=64, db_index=True, blank=True, verbose_name='物流单号')
    company = models.CharField(max_length=64, db_index=True, blank=True, verbose_name='物流名称')

    oid = models.CharField(max_length=64, db_index=True, blank=True, default='', verbose_name='子订单ID')
    outer_id = models.CharField(max_length=64, db_index=True, blank=True, verbose_name='商品编码')
    outer_sku_id = models.CharField(max_length=64, db_index=True, blank=True, verbose_name='规格编码')
    sku_id = models.IntegerField(null=True, db_index=True, verbose_name='SKUID')
    num = models.IntegerField(default=0, verbose_name='数量')
    title = models.CharField(max_length=64, blank=True, verbose_name='商品名称')
    property = models.CharField(max_length=64, blank=True, verbose_name='规格名称')

    can_reuse = models.BooleanField(default=False, verbose_name='二次销售')
    is_finish = models.BooleanField(default=False, verbose_name='处理完成')
    reason = models.IntegerField(choices=REFUND_REASON, default=0, verbose_name='退货原因')
    created = models.DateTimeField(null=True, blank=True, auto_now_add=True, verbose_name='创建时间')
    modified = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name='修改时间')

    memo = models.TextField(max_length=1000, blank=True, verbose_name='备注')

    class Meta:
        db_table = 'shop_refunds_product'
        app_label = 'refunds'
        verbose_name = u'退货商品'
        verbose_name_plural = u'退货商品列表'

    def __unicode__(self):

        info_list = [self.buyer_nick, self.buyer_mobile, self.buyer_phone,
                     str(self.trade_id), self.out_sid, self.company]
        info_string = '-'.join([s for s in info_list if s])
        return '<%s,%s,%s>' % (info_string, self.outer_id, self.outer_sku_id)

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                setattr(self, field.name, getattr(self, field.name).strip())

    @staticmethod
    def get_total(sku_id, can_reuse=True, begin_time=datetime.datetime(2016, 4, 20)):
        res = RefundProduct.objects.filter(
            sku_id=sku_id, can_reuse=can_reuse, created__gt=begin_time).aggregate(n=Sum("num")).get('n',0)
        return res or 0

    @cached_property
    def sale_trade(self):
        if not hasattr(self, '_sale_trade_'):
            from flashsale.pay.models import SaleTrade
            self._sale_trade_ = SaleTrade.objects.filter(tid=self.trade_id).first()
        return self._sale_trade_

    def get_sale_refund(self):
        trade_id = self.sale_trade.id if self.sale_trade else 0
        from flashsale.pay.models import SaleRefund
        if not hasattr(self, '_sale_refund_'):
            self._sale_refund_ = SaleRefund.objects.filter(trade_id=trade_id, sku_id=self.sku_id).first()
        return self._sale_refund_

    def send_goods_backed_message(self):
        """
        功能：　发送　用户的退货　已经到达仓库的　消息给用户
        """
        from shopapp.weixin.weixin_push import WeixinPush
        from flashsale.xiaolumm.models import WeixinPushEvent

        salerefund = self.get_sale_refund()
        if not salerefund:
            return
        push = WeixinPush()
        push.push_refund_notify(salerefund, WeixinPushEvent.SALE_REFUND_ARRIVE)
        return

    def check_salerefund_conformably(self):
        """
        功能：　检查是否  和　退款单　信息一致　（检查）
        """
        sale_refund = self.get_sale_refund()
        if not sale_refund:
            return False
        # 数量　物流单号
        if self.out_sid == sale_refund.sid and self.num == sale_refund.refund_num:
            return True
        return False


def update_warehouse_receipt_status(sender, instance, created, **kwargs):
    """ 仓库接收客户退货拆包更新 warehouse APP 中的 ReceiptGoods 相同快递单记录的拆包状态到 拆包状态 """
    if created:
        from shopback.warehouse.models import ReceiptGoods
        ReceiptGoods.update_status_by_open(instance.out_sid)


post_save.connect(update_warehouse_receipt_status, sender=RefundProduct,
                  dispatch_uid='post_save_update_warehouse_receipt_status')


def update_productskustats_refund_quantity(sender, instance, created, **kwargs):
    from shopback.items.models import ProductSku, ProductSkuStats
    if instance.created < ProductSkuStats.PRODUCT_SKU_STATS_COMMIT_TIME:
        return
    from shopback.items.tasks_stats import task_refundproduct_update_productskustats_return_quantity
    from shopback.items.tasks import task_update_inferiorsku_return_quantity
    sku_id = ProductSku.get_by_outer_id(instance.outer_id, instance.outer_sku_id).id
    if sku_id:
        RefundProduct.objects.filter(id=instance.id).update(sku_id=sku_id)
        task_refundproduct_update_productskustats_return_quantity.delay(sku_id)
        task_update_inferiorsku_return_quantity.delay(sku_id)
    else:
        logger.error(u"RefundProduct update_productskustats_refund_quantity error :" + str(RefundProduct.id))


post_save.connect(update_productskustats_refund_quantity, sender=RefundProduct, dispatch_uid='post_save_update_productskustats_refund_quantity')
