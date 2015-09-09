#coding=utf-8
from shopback import paramconfig as pcfg
from .models import RefundProduct, Refund, GOOD_STATUS_CHOICES
from shopback.trades.models import MergeOrder, MergeTrade
from shopback.base import log_action,User, ADDITION, CHANGE
import logging

logger = logging.getLogger('django.request')


#   1 简化订单退换货操作流程，即退货商品录入时就创建退换货单(shopback/refunds/ ,Refund,RefundProduct)
#   2 更新订单退货状态到订单列表（MergeTrade）,修改status的状态为退款关闭 status = pcfg.TRADE_CLOSED

def update_Unrelate_Prods_Product(pro, req, trade_id=''):
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
    refunds = Refund.objects.filter(tid=trade_id)
    if refunds.count() > 0:     # 如果存在退货款单记录
        pass                    # 不做处理
    else:                       # 没有记录则创建一条记录
        # 根据原单 trade_id 找 MergeTrade
        reason = pro.reason  #
        reason_str = REFUND_REASON[int(reason)][1]
        merge_trades = MergeTrade.objects.filter(tid=trade_id)
        if merge_trades.count() == 0:
            return
        merge_trade  = merge_trades[0]    
        # 根据merge_trade 找 MergeOrder
        merge_order = MergeOrder.objects.filter(merge_trade=merge_trade, outer_id=pro.outer_id, outer_sku_id=pro.outer_sku_id)
        # 确认 MergeOrder 的存在后 创建 退货款单
        try:
            if merge_order.count() > 0:
                # 根据 MergeOrder 的情况创建 退货款单
                refund = Refund()
                refund.tid = merge_trade.tid                     # 交易ID
                refund.title = merge_order[0].title                             # 标题
                refund.num_iid = merge_order[0].num_iid or 0                    # 商品ID=商品编码
                refund.user = merge_trade.user                   # 店铺
                # refund.seller_id =                                            # 卖家ID
                refund.buyer_nick = merge_trade.buyer_nick                   # 买家昵称
                refund.seller_nick = merge_trade.seller_nick                 # 卖家昵称

                refund.mobile = merge_trade.receiver_mobile      # 收件人手机  （这里不使用退货物流的手机号码）
                refund.phone  = merge_trade.receiver_phone        # 电话

                refund.total_fee = merge_order[0].total_fee                     # 订单总费用
                # refund.refund_fee                                             # 退款费用
                refund.payment = merge_order[0].payment                         # 实付款
                refund.oid = merge_order[0].oid                                 # 订单ID
                refund.company_name = pro.company                               # 仓库收到退回产品的发货物流公司
                refund.sid = pro.out_sid                                        # 仓库收到退回产品的快递单号
                refund.reason = reason_str                                      # 退货原因
                # refund.desc =                                                 # 描述
                refund.has_good_return = True                                   # 是否退货（是）
                refund.good_status = GOOD_STATUS_CHOICES[2][0]                  # 退货商品的状态（买家已经退货）
                # refund.order_status = Refund.                                 # 退货商品的订单状态
                refund.cs_status = 2                                            # 需要客服介入
                refund.status = pcfg.REFUND_CONFIRM_GOODS                       # 买家已经退货
                refund.save()                                                   # 保存数据

                # merge_trade[0].status = pcfg.TRADE_CLOSED                       # 修改MergeTrade status 为关闭
                # merge_trade[0].save()                                           # 保存
                action_desc = u"创建交易ID为：{0} 商品标题为：{1}的 Refund ".format(trade_id,merge_order[0].title)
                log_action(req.user.id, refund, ADDITION, action_desc)                  # 创建操作日志
        except Exception, exc:
            logger.error(exc.message, exc_info=True)