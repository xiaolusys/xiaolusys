# coding=utf-8
from .models_freesample import ReadPacket, AwardWinner
from django.db.models import Sum, F
from flashsale.pay.models_user import BudgetLog
from decimal import Decimal
import logging

logger = logging.getLogger('__name__')


def pmt_red_to_budgetlog():
    """
    活动红包记录到钱包记录中,并且计算金额到用户的账户
    """
    # 找出没有兑换的活动红包记录
    reds = ReadPacket.objects.filter(status=ReadPacket.NOT_EXCHANGE)
    # 按计算记录的金额 按照用户和日期分组 {'created_d': datetime.date(2016, 2, 27), 'customer': u'1', 'sum_value': 5.92}
    cus_reds = reds.extra(select={'created_d': 'date(created)'}).values('created_d',
                                                                        'customer').annotate(sum_value=Sum('value'))
    for cus_red in cus_reds:
        customer_id = cus_red['customer']
        flow_amount = int(Decimal(str(cus_red['sum_value'])) * 100)  # 注意小数转换
        # 创建BudgetLog记录
        BudgetLog.objects.create(customer_id=customer_id,
                                 flow_amount=flow_amount,
                                 budget_type=BudgetLog.BUDGET_IN,
                                 budget_log_type=BudgetLog.BG_ENVELOPE,
                                 budget_date=cus_red['created_d'],
                                 referal_id=cus_red['created_d'].strftime("%Y-%m-%d"))
    # 更新到兑换状态
    reds.update(status=ReadPacket.EXCHANGE)
    return


from flashsale.pay.models_coupon_new import UserCoupon
from flashsale.pay.models import SaleTrade, SaleOrder, SaleRefund


def delete_customer_active_coupon(customer_id):
    """
    删除用户的活动优惠券
    """
    ucps = UserCoupon.objects.filter(customer=customer_id,
                                     cp_id__template__id=27)  # 卡通浴巾188元 id 40
    for ucp in ucps:
        ucp.cp_id.delete()  # 删除券池数据
        ucp.delete()  # 删除优惠


def get_customer_product_order(customer_id):
    """
    获取用户的浴巾活动的orders
    """
    orders = SaleOrder.objects.filter(sale_trade__buyer_id=customer_id,
                                      payment__lte=1,  # 使用过优惠券的记录
                                      item_id__in=[14501, 14502, 14503, 14504, 14505, 23147],
                                      status__in=[SaleOrder.WAIT_SELLER_SEND_GOODS,  # 已付款
                                                  SaleOrder.WAIT_BUYER_CONFIRM_GOODS,  # 已发货
                                                  SaleOrder.TRADE_BUYER_SIGNED,  # 确认签收
                                                  SaleOrder.TRADE_FINISHED]).order_by('created')  # 交易成功
    return orders


from core.options import log_action, CHANGE, ADDITION, get_systemoa_user


def make_budget_log(order):
    """钱包支付的使用退款到钱包"""
    if order.sale_trade.channel == SaleTrade.BUDGET:  # 退回小鹿钱包
        referal_id = 'order' + str(order.id)
        BudgetLog.objects.create(customer_id=order.sale_trade.buyer_id,
                                 flow_amount=order.payment * 100,
                                 budget_type=BudgetLog.BUDGET_IN,
                                 budget_log_type=BudgetLog.BG_REFUND,
                                 status=BudgetLog.CONFIRMED,
                                 referal_id=referal_id)
        return True
    return False


def make_sale_order_refund(order):
    """
    根据订单生成退款单
    """
    refunds = SaleRefund.objects.filter(order_id=order.id)
    if refunds.exists():
        refund = refunds[0]
        refund_id = refund.id
        return refund_id
    else:
        is_budget = make_budget_log(order)  # 如果是下来了钱包退回小鹿钱包
        if is_budget:
            return ''
        refund = SaleRefund.objects.create(trade_id=order.sale_trade.id,
                                           order_id=order.id,
                                           buyer_id=order.sale_trade.buyer_id,
                                           item_id=order.item_id,
                                           title=order.title,
                                           sku_id=order.sku_id,
                                           sku_name=order.sku_name,
                                           refund_num=order.num,
                                           refund_fee=order.payment,
                                           mobile=order.sale_trade.receiver_mobile,
                                           status=SaleRefund.REFUND_WAIT_SELLER_AGREE)
        channel = order.sale_trade.channel
        refund.channel = channel
        refund.save()
        action_user = get_systemoa_user()
        log_action(action_user, refund, ADDITION, u'活动浴巾作废订单处理')
        refund_id = refund.id
        return refund_id


def close_merge_trade(tid):
    """
    关闭Mergetrade　到退款关闭状态
    """
    from shopback.trades.models import MergeTrade
    from shopback import paramconfig as pcfg

    try:
        mt = MergeTrade.objects.get(tid=tid)
        mt.status = pcfg.TRADE_CLOSED
        mt.save()
        action_user = get_systemoa_user()
        log_action(action_user, mt, CHANGE, u'作废活动订单,退款关闭')
        trade_id = mt.id
        return trade_id
    except Exception, exc:
        logger.warn(exc)
        return 0


import csv


def record_to_csv(filename, data):
    csvfile = file(filename, 'wb')
    writer = csv.writer(csvfile)
    writer.writerow(['用户id', '中奖状态', 'merge_trade_link', 'sale_trade_link', 'sale_refund_link'])
    writer.writerows(data)
    csvfile.close()


def close_saleorder_by_obsolete_awards():
    """
    2016-4-20
    处理活动中奖的作废的中奖记录关闭SaleOrder
    """
    merge_trade_link = 'http://youni.huyi.so/admin/trades/mergetrade/?id__in={0}'
    sale_trade_link = 'http://youni.huyi.so/admin/pay/saletrade/?id__in={0}'
    sale_refund_link = 'http://youni.huyi.so/admin/pay/salerefund/?id__in={0}'  # 42247,42248

    awards1 = AwardWinner.objects.filter(status=1)  # 已经领取中奖信息
    awards2 = AwardWinner.objects.filter(status=2)  # 已经作废中奖信息

    for award in awards1:  # 领取的
        customer_id = award.customer_id
        award_status = '已领取'
        s_orders = get_customer_product_order(customer_id)
        if s_orders.count() > 1:  # 如果用户有超过一个的浴巾活动的订单
            store_data = []
            sale_trade_ids_1 = []
            refund_ids_1 = []

            for order in s_orders[1::]:
                refund_id = make_sale_order_refund(order)
                order.refund_status = SaleRefund.REFUND_WAIT_SELLER_AGREE
                order.save()
                action_user = get_systemoa_user()
                log_action(action_user.id, order, CHANGE, u'活动浴巾修改该订单到申请退款状态')

                sale_trade_ids_1.append(str(order.sale_trade.id))
                refund_ids_1.append(str(refund_id))

            store_data.append(
                (
                    str(customer_id),
                    award_status,
                    '',
                    sale_trade_link.format(','.join(sale_trade_ids_1)),
                    sale_refund_link.format(','.join(refund_ids_1))
                )
            )
            record_to_csv('handler_acitve_apply.csv', store_data)

    for award in awards2:  # 已经作废
        customer_id = award.customer_id
        award_status = '已作废'
        # 删除该用户所有浴巾活动优惠券（含券池）
        delete_customer_active_coupon(customer_id)
        # 查找该用户所有浴巾活动订单
        orders = get_customer_product_order(customer_id)

        # 生成退款单
        sale_trade_ids = []
        merge_trade_ids = []
        refund_ids = []

        data = []
        for order in orders:
            refund_id = make_sale_order_refund(order)
            # sale_order 切换到退款状态
            order.refund_status = SaleRefund.REFUND_WAIT_SELLER_AGREE
            order.save()
            action_user = get_systemoa_user()
            log_action(action_user.id, order, CHANGE, u'活动浴巾修改该订单到申请退款状态')

            # 关闭 Mergetrade
            tid = order.sale_trade.tid
            merge_trade_id = close_merge_trade(tid)

            sale_trade_ids.append(str(order.sale_trade.id))
            merge_trade_ids.append(str(merge_trade_id))
            refund_ids.append(str(refund_id))

        data.append(
            (
                str(customer_id),
                award_status,
                merge_trade_link.format(','.join(merge_trade_ids)),
                sale_trade_link.format(','.join(sale_trade_ids)),
                sale_refund_link.format(','.join(refund_ids))
            )
        )
        record_to_csv('handler_obsolete_apply.csv', data)
