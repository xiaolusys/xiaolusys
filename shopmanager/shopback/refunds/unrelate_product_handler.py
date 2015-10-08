#coding=utf-8
from shopback import paramconfig as pcfg
from .models import RefundProduct, Refund, GOOD_STATUS_CHOICES
from shopback.trades.models import MergeOrder, MergeTrade
from shopback.base import log_action,User, ADDITION, CHANGE
import logging

logger = logging.getLogger('django.request')


#   1 简化订单退换货操作流程，即退货商品录入时就创建退换货单(shopback/refunds/ ,Refund,RefundProduct)
#   2 更新订单退货状态到订单列表（MergeTrade）,修改status的状态为退款关闭 status = pcfg.TRADE_CLOSED
def get_mergeorder_by_refundproduct(refund_product):
    trade_id = refund_product.trade_id
    merge_trades = MergeTrade.objects.filter(tid=trade_id)
    if merge_trades.count() == 0:
        return
    merge_trade  = merge_trades[0] 
    # 根据merge_trade 找 MergeOrder
    merge_orders = MergeOrder.objects.filter(merge_trade=merge_trade, 
                                            outer_id=refund_product.outer_id, 
                                            outer_sku_id=refund_product.outer_sku_id)
    if merge_orders.count() == 0:
        return
    merge_order = merge_orders[0]

    return merge_order

def get_refund_by_refundproduct(refund_product):
    
    merge_order = get_mergeorder_by_refundproduct(refund_product)
    if not merge_order:
        return
    trade_id = merge_order.merge_trade.tid
    refunds = Refund.objects.filter(tid=trade_id,oid=merge_order.oid) 
    if refunds.count() == 0:
        return
    return refunds[0]

    
def update_Unrelate_Prods_Product(pro, req):
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
    refund = get_refund_by_refundproduct(pro)
    if refund :     # 如果系统已经创建该退款单
        refund.has_good_return = True 
        refund.save()
    else:   # 没有记录则创建一条记录
        # 根据原单 trade_id 找 MergeTrade
        reason = pro.reason  #
        reason_str = REFUND_REASON[int(reason)][1]
        # 确认 MergeOrder 的存在后 创建 退货款单
        merge_order = get_mergeorder_by_refundproduct(pro)
        if not merge_order:
            return
        merge_trade = merge_order.merge_trade
        try:
            # 根据 MergeOrder 的情况创建 退货款单
            refund = Refund()
            refund.tid = merge_trade.tid                     # 交易ID
            refund.title = merge_order.title                             # 标题
            refund.num_iid = merge_order.num_iid or 0                    # 商品ID=商品编码
            refund.user = merge_trade.user                   # 店铺
            # refund.seller_id =                                            # 卖家ID
            refund.buyer_nick = merge_trade.buyer_nick                   # 买家昵称
            refund.seller_nick = merge_trade.user.nick                   # 卖家昵称

            refund.mobile = merge_trade.receiver_mobile      # 收件人手机  （这里不使用退货物流的手机号码）
            refund.phone  = merge_trade.receiver_phone        # 电话

            refund.total_fee = merge_order.total_fee                     # 订单总费用
            # refund.refund_fee                                             # 退款费用
            refund.payment = merge_order.payment                         # 实付款
            refund.oid = merge_order.oid                                 # 订单ID
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
            action_desc = u"创建交易ID为：{0} 商品标题为：{1}的 Refund ".format(merge_trade.tid,merge_order.title)
            log_action(req.user.id, refund, ADDITION, action_desc)                  # 创建操作日志
        except Exception, exc:
            logger.error(exc.message, exc_info=True)


from shopback.items.models import Product, ProductSku
from django.db.models import F
from common.modelutils import update_model_fields


def update_Product_Collect_Num(pro, req):
    """
    仓库拆包的时候更新库存数量
    """
    try:
        product = Product.objects.get(outer_id=pro.outer_id)
        psk = ProductSku.objects.get(product_id=product.id, outer_id=pro.outer_sku_id)
        if pro.can_reuse:  # 判断是二次销售　　则　添加库存数
            # 添加sku的库存数量
            psk_quantity = psk.quantity
            psk.quantity = F("quantity") + pro.num
            update_model_fields(psk, update_fields=['quantity'])    # 更新字段方法
            action_desc = u"拆包退货商品添加->将原来库存{0}更新为{1}".format(psk_quantity, psk.quantity)
            log_action(req.user.id, psk, CHANGE, action_desc)

            # 添加库存商品的数量
            pro_collect_num = product.collect_num   # 原来的库存数量
            product.collect_num = F("collect_num") + pro.num
            update_model_fields(product, update_fields=['collect_num'])    # 更新字段方法
            pro_action_desc = u"拆包退货商品添加->将原来库存{0}更新为{1}".format(pro_collect_num, product.collect_num)
            log_action(req.user.id, product, CHANGE, pro_action_desc)
        else:  # 如果不能二次销售　则　添加次品数　
            sku_inferior_num = psk.sku_inferior_num
            psk.sku_inferior_num = F("sku_inferior_num") + pro.num
            update_model_fields(psk, update_fields=['sku_inferior_num'])    # 更新字段方法
            action_desc = u"拆包退货商品添加->将原来次品数量{0}更新为{1}".format(sku_inferior_num, psk.sku_inferior_num)
            log_action(req.user.id, psk, CHANGE, action_desc)
    except Product.DoesNotExist or ProductSku.DoesNotExist:
        return



def update_Product_Collect_Num_By_Delete(pro, req):
    """
    拆包的时候出错要删除退货商品　，　同时更新库存的数量
    """
    try:
        product = Product.objects.get(outer_id=pro.outer_id)
        psk = ProductSku.objects.get(product_id=product.id, outer_id=pro.outer_sku_id)
        if pro.can_reuse:  # 判断是二次销售　　则　减去库存数
            # 删除库存sku的数量
            psk_quantity = psk.quantity
            psk.quantity = F("quantity") - pro.num
            if psk.quantity < 0:
                psk.quantity = 0
            update_model_fields(psk, update_fields=['quantity'])    # 更新字段方法
            action_desc = u"拆包退货商品删除->将原来库存{0}更新为{1}".format(psk_quantity, psk.quantity)
            log_action(req.user.id, psk, CHANGE, action_desc)

            # 删除库存商品的数量
            pro_collect_num = product.collect_num   # 原来的库存数量
            product.collect_num = F("collect_num") - pro.num
            update_model_fields(product, update_fields=['collect_num'])    # 更新字段方法
            pro_action_desc = u"拆包退货商品删除->将原来库存{0}更新为{1}".format(pro_collect_num, product.collect_num)
            log_action(req.user.id, product, CHANGE, pro_action_desc)
        else:  # 如果不能二次销售　则　减去次品数　
            sku_inferior_num = psk.sku_inferior_num
            psk.sku_inferior_num = F("sku_inferior_num") - pro.num
            update_model_fields(psk, update_fields=['sku_inferior_num'])    # 更新字段方法
            action_desc = u"拆包退货商品删除->将原来次品数量{0}更新为{1}".format(sku_inferior_num, psk.sku_inferior_num)
            log_action(req.user.id, psk, CHANGE, action_desc)
    except Product.DoesNotExist or ProductSku.DoesNotExist:
        return
