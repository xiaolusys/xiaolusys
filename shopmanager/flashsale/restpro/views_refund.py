# coding=utf-8
from rest_framework.response import Response
from shopback.refunds.models import Refund, REFUND_REASON
from flashsale.pay.models import SaleOrder, SaleTrade


def refund_Handler(request):
    length = int(request.data["refund[0][length]"])
    reason = int(request.data["refund[0][reason]"])
    refund_or_pro = int(request.data["refund[0][refund_or_pro]"])
    print refund_or_pro, "refund_or_prorefund_or_prorefund_or_prorefund_or_pro"
    if refund_or_pro == 0:
        for i in range(1, length + 1):
            oid = int(request.data["refund[" + str(i) + "][id]"])
            num = int(request.data["refund[" + str(i) + "][num]"])
            price = float(request.data["refund[" + str(i) + "][sum_price]"])
            ref_product = SaleOrder.objects.get(id=oid)
            trade = ref_product.sale_trade
            discount_fee = trade.discount_fee  # 总折扣价格
            if trade.status == SaleTrade.WAIT_SELLER_SEND_GOODS:  # 已付款状态
                # 交易中子订单的个数
                if ref_product.status == SaleOrder.TRADE_REFUNDING:  # 如果是　退款申请中　返回　
                    return {'res': "refunding"}
                if num == 0:  # 如过退的数量是0则　退出本次循环
                    break
                # 找到这一个order 的单件折扣价格
                refund = Refund()
                refund.tid = trade.id
                refund.title = ref_product.title
                refund.num_iid = ref_product.item_id or 0
                # refund.user = trade.user
                refund.seller_id = trade.buyer_id
                refund.buyer_nick = trade.buyer_nick
                refund.mobile = trade.receiver_mobile
                refund.phone = trade.receiver_phone
                refund.total_fee = trade.total_fee
                # 订单中的单价　数量
                # 退款金额为 价格* 数量　减去　折扣费用　注意这里如果是交易里面有多个订单退单都会减去折扣
                refund.refund_fee = str((ref_product.payment / ref_product.num) * num)
                refund.payment = ref_product.payment
                refund.oid = oid
                refund.company_name = trade.logistics_company.name if trade.logistics_company else u"暂无"
                refund.sid = trade.out_sid
                refund.reason = REFUND_REASON[reason][1]
                # refund.good_status =
                # refund.order_status =
                # refund.cs_status =
                refund.status = Refund.REFUND_WAIT_SELLER_AGREE
                # 生成退货款单
                refund.save()
                ref_product.status = SaleOrder.TRADE_REFUNDING  # 修改该明细状态到退款申请中
                ref_product.save()  # 保存
            else:  # 否则返回不在已付款状态的说明
                return {"res": "not_in_send"}
        trade.status = SaleTrade.TRADE_REFUNDING
        trade.save()
        return {"res": "refund_ok"}
    if refund_or_pro == 1:
        # 创建退货款单
        for i in range(1, length + 1):
            oid = int(request.data["refund[" + str(i) + "][id]"])
            num = int(request.data["refund[" + str(i) + "][num]"])
            price = float(request.data["refund[" + str(i) + "][sum_price]"])
            ref_product = SaleOrder.objects.get(id=oid)
            trade = ref_product.sale_trade
            if trade.status == SaleTrade.WAIT_BUYER_CONFIRM_GOODS:  # 已经发货状态
                # 交易中子订单的个数
                if ref_product.status == SaleOrder.TRADE_REFUNDING:  # 如果是　退款申请中　返回　
                    return {'res': "refunding"}
                if num == 0:  # 如过退的数量是0则　退出本次循环
                    break
                # 找到这一个order 的单件折扣价格
                refund = Refund()
                refund.tid = trade.id
                refund.title = ref_product.title
                refund.num_iid = ref_product.item_id or 0
                # refund.user = trade.user
                refund.seller_id = trade.buyer_id
                refund.buyer_nick = trade.buyer_nick
                refund.mobile = trade.receiver_mobile
                refund.phone = trade.receiver_phone
                refund.total_fee = trade.total_fee
                # 订单中的单价　数量
                # 退款金额为 价格* 数量　减去　折扣费用　注意这里如果是交易里面有多个订单退单都会减去折扣
                refund.refund_fee = str((ref_product.payment / ref_product.num) * num)
                refund.payment = ref_product.payment
                refund.oid = oid
                refund.company_name = trade.logistics_company.name if trade.logistics_company else u"暂无"
                refund.sid = trade.out_sid
                refund.reason = REFUND_REASON[reason][1]
                # refund.good_status =
                # refund.order_status =
                # refund.cs_status =
                refund.status = Refund.REFUND_WAIT_SELLER_AGREE
                # 生成退货款单
                refund.save()
                ref_product.status = SaleOrder.TRADE_REFUNDPROING  # 修改该明细状态到退退货申请中
                ref_product.save()  # 保存
            else:
                return {"res": "not_in_pro"}
        trade.status = SaleTrade.TRADE_REFUNDPROING  # 修改交易状态到退货申请中
        trade.save()
        return {"res": "refund_product_ok"}