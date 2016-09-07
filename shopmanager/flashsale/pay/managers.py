# -*- coding:utf8 -*-
import logging
from core.managers import BaseManager, CacheManager
from common.modelutils import update_model_fields
from flashsale.pay.signals import signal_saletrade_refund_post


logger = logging.getLogger(__name__)


class NormalSaleTradeManager(BaseManager):
    def get_queryset(self):
        _super = super(NormalSaleTradeManager, self)
        queryset = _super.get_queryset()
        return queryset.filter(
            status__in=self.model.NORMAL_TRADE_STATUS
        ).order_by('-created')


class NormalUserAddressManager(BaseManager):
    def get_queryset(self):
        queryset = super(NormalUserAddressManager, self).get_queryset()
        return queryset.filter(status=self.model.NORMAL).order_by('-created')


from . import constants


class ShopProductCategoryManager(BaseManager):
    def child_query(self):
        """ 童装产品 """
        pro_category = constants.CHILD_CID_LIST
        return self.get_queryset().filter(pro_category__in=pro_category).order_by("-position")

    def female_query(self):
        """ 女装产品 """
        pro_category = constants.FEMALE_CID_LIST
        return self.get_queryset().filter(pro_category__in=pro_category).order_by("-position")


class SaleRefundManager(BaseManager):
    def create_or_update_by_order(self, good_status=None, sale_order_id=None
                                  , reason=None, refund_num=None, refund_fee=None,
                                   desc=None, proof_pic=None, status=None, refund_channel=None):
        if not sale_order_id:
            raise Exception(u'SaleRefundManager: %s order id not found :' % sale_order_id)

        from flashsale.pay.models import SaleOrder, SaleTrade, TradeCharge
        order = SaleOrder.objects.get(id=sale_order_id)
        trade = order.sale_trade
        if trade.channel not in (SaleTrade.BUDGET, SaleTrade.WALLET):  # 如果不是　小鹿钱包或者妈妈钱包支付　就要检查charge
            charge = TradeCharge.objects.filter(order_no=trade.tid, paid=True).first()  # 确认支付的交易charge
            if not charge:  # 没有支付记录
                raise Exception(u'SaleRefundManager: saletrade tid %s charge not found' % trade.tid)

        refund = self.filter(order_id=sale_order_id).first()
        from shopback.refunds.models import REFUND_REASON
        if refund:
            logger.warn(u'SaleRefundManager: refund %s was exists!' % sale_order_id)
            # 如果存在退款单则比较　有改变的字段则更新
            update_fields = []
            params = {
                "buyer_id": trade.buyer_id,
                "charge": trade.charge,
                "channel": trade.channel,
                "item_id": order.item_id,
                "title": order.title,
                "ware_by": order.item_ware_by,
                "sku_id": order.sku_id,
                "sku_name": order.sku_name,
                "refund_num": refund_num,
                "buyer_nick": trade.buyer_nick,
                "mobile": trade.receiver_mobile,
                "phone": trade.receiver_phone,
                "total_fee": order.total_fee,
                "payment": order.payment,
                "refund_fee": refund_fee,
                "good_status": good_status,
                "status": status,
                "desc": desc,
                "proof_pic": proof_pic,
                "refund_channel":refund_channel,
                "has_good_return": order.stats_post_goods(),
            }
            for k, v in params.iteritems():
                if v is None:
                    continue
                if hasattr(refund, k) and getattr(refund, k) != v:
                    setattr(refund, k, v)
                    update_fields.append(k)
            if not isinstance(int(reason), int):
                logger.error(u'SaleRefundManager: update the refund  %s　reason not int type' % refund.id)
            else:
                try:
                    if refund.reason != REFUND_REASON[reason][1]:
                        refund.reason = REFUND_REASON[reason][1]
                except IndexError:
                    refund.reason = REFUND_REASON[0][1]
                update_fields.append('reason')
                if update_fields:
                    refund.save(update_fields=update_fields)
            return refund, False
        else:
            refund = self.model(
                trade_id=trade.id,
                order_id=order.id,
                buyer_id=trade.buyer_id,
                charge=trade.charge,
                channel=trade.channel,
                item_id=order.item_id,
                title=order.title,
                ware_by=order.item_ware_by,
                sku_id=order.sku_id,
                sku_name=order.sku_name,
                refund_num=refund_num,
                buyer_nick=trade.buyer_nick,
                mobile=trade.receiver_mobile,
                phone=trade.receiver_phone,
                total_fee=order.total_fee,
                payment=order.payment,
                refund_fee=refund_fee,
                good_status=good_status,
                reason=REFUND_REASON[reason][1],
                desc=desc,
                proof_pic=proof_pic,
                refund_channel=refund_channel,
                has_good_return=order.stats_post_goods(),
            )
            refund.save()
            signal_saletrade_refund_post.send(sender=self.model, obj=refund)
            return refund, True


class CustomerManager(CacheManager):

    @property
    def normal_customer(self):
        queryset = super(CustomerManager, self).get_queryset()
        return queryset.filter(status=self.model.NORMAL).order_by('-created')

