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
    refunds = Refund.objects.filter(tid=trade_id)
    if refunds.count() > 0:     # 如果存在退货款单记录
        pass                    # 不做处理
    else:                       # 没有记录则创建一条记录
        # 根据原单 trade_id 找 MergeTrade
        merge_trade = MergeTrade.objects.filter(tid=trade_id)
        # 根据merge_trade 找 MergeOrder
        merge_order = MergeOrder.objects.filter(merge_trade_id=merge_trade[0].id, outer_id=pro.outer_id, outer_sku_id=pro.outer_sku_id)
        # 确认 MergeOrder 的存在后 创建 退货款单
        try:
            if merge_order.count() > 0:
                # 根据 MergeOrder 的情况创建 退货款单
                refund = Refund()
                refund.tid = merge_order[0].merge_trade.tid                     # 交易ID
                refund.title = merge_order[0].title                             # 标题
                refund.num_iid = merge_order[0].num_iid or 0                         # 商品ID=商品编码
                refund.user = merge_order[0].merge_trade.user                   # 店铺
                # refund.seller_id =                                            # 卖家ID
                refund.buyer_nick = merge_order[0].buyer_nick                   # 买家昵称
                refund.seller_nick = merge_order[0].seller_nick                 # 卖家昵称

                refund.mobile = merge_order[0].merge_trade.receiver_mobile      # 收件人手机  （这里不使用退货物流的手机号码）
                refund.phone = merge_order[0].merge_trade.receiver_phone        # 电话

                refund.total_fee = merge_order[0].total_fee                     # 订单总费用
                # refund.refund_fee                                             # 退款费用
                refund.payment = merge_order[0].payment                         # 实付款
                refund.oid = merge_order[0].oid                                 # 订单ID
                refund.company_name = pro.company                               # 仓库收到退回产品的发货物流公司
                refund.sid = pro.out_sid                                        # 仓库收到退回产品的快递单号
                # refund.reason =                                               # 退货原因
                # refund.desc =                                                 # 描述
                refund.good_status = GOOD_STATUS_CHOICES[2][0]                  # 退货商品的状态（买家已经退货）
                # refund.order_status = Refund.                                 # 退货商品的订单状态
                refund.cs_status = 2                                            # 需要客服介入
                refund.status = pcfg.NO_REFUND                                  # 没有退款
                refund.save()                                                   # 保存数据

                # merge_trade[0].status = pcfg.TRADE_CLOSED                       # 修改MergeTrade status 为关闭
                # merge_trade[0].save()                                           # 保存
                action_desc = u"创建交易ID为：{0} 商品标题为：{1}的 Refund ".format(trade_id,merge_order[0].title)
                log_action(req.user.id, refund, ADDITION, action_desc)                  # 创建操作日志
        except Exception, exc:
            logger.error(exc.message, exc_info=True)