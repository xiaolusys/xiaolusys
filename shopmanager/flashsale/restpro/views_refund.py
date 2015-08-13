# coding=utf-8
from rest_framework.response import Response
from flashsale.pay.models_refund import SaleRefund
from flashsale.pay.models import SaleOrder, SaleTrade
from shopback.refunds.models import REFUND_REASON

"""
    REFUND_STATUS = (
        (NO_REFUND,'没有退款'),
        (REFUND_WAIT_SELLER_AGREE,'买家已经申请退款'),
        (REFUND_WAIT_RETURN_GOODS,'卖家已经同意退款'),
        (REFUND_CONFIRM_GOODS,'买家已经退货'),
        (REFUND_REFUSE_BUYER,'卖家拒绝退款'),
        (REFUND_APPROVE,'确认退款，等待返款'),
        (REFUND_CLOSED,'退款关闭'),
        (REFUND_SUCCESS,'退款成功'),
    )
    refund_id     = models.BigIntegerField(null=True,verbose_name=u'退款ID')
    refund_fee    = models.FloatField(default=0.0,verbose_name=u'退款费用')
    refund_status = models.IntegerField(choices=SaleRefund.REFUND_STATUS,
                                       default=SaleRefund.NO_REFUND,
                                       blank=True,verbose_name='退款状态')
"""


def create_Sale_Refund(trade_id=None, order_id=None):
    """
    参数：trade_id:交易id   order_id:子订单id
    功能：修改特卖/退款单状态
    返回：False:创建失败  sale_refund
         True:创建成功 sale_refund
    """
    sale_refund, state = SaleRefund.objects.get_or_create(trade_id=trade_id, order_id=order_id)
    return sale_refund, state


def get_Sale_Refund(trade_id=None, order_id=None, sale_refund_id=None):
    """
    参数：trade_id:交易id   order_id:子订单id
    功能：获取退款单
    返回：False:没有找到
         True:找到
    """
    try:
        if sale_refund_id is None:  # 没有
            sale_refund = SaleRefund.objects.get(trade_id=trade_id, order_id=order_id)
            return True
        elif sale_refund_id is not None:
            sale_refund = SaleRefund.objects.get(id=sale_refund_id)
            return sale_refund
    except SaleRefund.DoesNotExist:
        return False


def get_Refund_Order_Trade(order_id=None):
    """
    参数：子订单id
    功能：获取子订单对象,交易对象,交易的子订单数量
    返回：order.obj   trade.obj   order.count
    """
    order = SaleOrder.objects.get(id=order_id)
    trade = order.sale_trade
    order_count = trade.sale_orders.all().count()
    return trade, order, order_count


def judge_Refund(order_id=None):
    """
    参数：子订单id
    功能：判断子订单能否退款
    返回：False:不能退款
         True:可以退款   　
    """
    # 查看sale_trade 的状态 WAIT_SELLER_SEND_GOODS  已付款的才可以退款
    # 查看sale_order 的状态　WAIT_SELLER_SEND_GOODS　已经付款的才可以退款
    # 查看退款单　　如果不存存在该退款单(没有申请过)　　则允许申请　
    trade, order, order_count = get_Refund_Order_Trade(order_id=order_id)
    t_status = True if trade.status == SaleTrade.WAIT_SELLER_SEND_GOODS else False
    o_status = True if order.status == SaleOrder.WAIT_SELLER_SEND_GOODS else False
    refund = get_Sale_Refund(trade_id=trade.id, order_id=order.id)
    if t_status and o_status and not refund:
        return True
    else:
        return False


def judge_Refund_Product(order_id=None):
    """
    参数：子订单id
    功能：判断子订单能否退货
    返回：False:不能退货
         True:可以退货
    """
    # 查看sale_trade 的状态 WAIT_BUYER_CONFIRM_GOODS  已发货的才可以退货
    # 查看sale_order 的状态　WAIT_BUYER_CONFIRM_GOODS　已经发货的才可以退货
    # 查看退款单　　如果不存存在该退款单　　则允许申请退货　
    trade, order, order_count = get_Refund_Order_Trade(order_id=order_id)
    t_status = True if trade.status == SaleTrade.WAIT_BUYER_CONFIRM_GOODS else False
    o_status = True if order.status == SaleOrder.WAIT_BUYER_CONFIRM_GOODS else False
    refund = get_Sale_Refund(trade_id=trade.id, order_id=order.id)
    if t_status and o_status and not refund:
        return True
    else:
        return False


def modify_Sale_Refund_Status(sale_refund_id=None, status=None):
    """
    参数：
    功能：修改特卖/退款单状态
    返回：False:修改失败
         True:修改成功
    """
    sale_refund = get_Sale_Refund(sale_refund_id=sale_refund_id)
    if sale_refund:
        sale_refund.status = status
        sale_refund.save()
        return True
    else:
        return False


def save_Other_Atriibut(trade=None, order=None, sale_refund=None, refund_num=None, reason=None):
    sale_refund.buyer_id = trade.buyer_id
    sale_refund.title = order.title
    sale_refund.charge = trade.charge
    sale_refund.item_id = int(order.item_id) if order.item_id else 0
    sale_refund.sku_id = int(order.sku_id) if order.sku_id else 0
    sale_refund.sku_name = order.sku_name
    sale_refund.refund_num = refund_num
    sale_refund.buyer_nick = trade.buyer_nick
    sale_refund.mobile = trade.receiver_mobile
    sale_refund.phone = trade.receiver_phone
    sale_refund.total_fee = order.total_fee
    sale_refund.payment = order.payment
    sale_refund.refund_fee = order.refund_fee
    sale_refund.reason = REFUND_REASON[reason][1]  # 填写原因
    sale_refund.good_status = SaleRefund.BUYER_NOT_RECEIVED
    sale_refund.status = SaleRefund.REFUND_WAIT_SELLER_AGREE
    sale_refund.save()


def save_Resund_Product_Atribut(refund=None, company=None, sid=None):
    """
    参数：物流信息　是否退货　是否换货
    功能：对于退货产品要保留的一些额外的信息
    返回：None
    """
    refund.company_name = company
    refund.sid = sid
    refund.has_good_return = True  # 退货
    refund.status = SaleRefund.REFUND_CONFIRM_GOODS
    refund.save()


def judge_Logistics(company=None, sid=None):
    """
    功能：对物流信息验证过程
    参数：物流公司company 快递单号 sid
    返回：有效：True  无效：False
    """
    pass


def sub_Handler(request=None, reason=None, categry=None):
    oid = int(request.data.get("refund[1][id]"))
    num = int(request.data.get("refund[1][num]"))
    price = float(request.data.get("refund[1][sum_price]"))

    # 退货要填写退货的　　物流信息　快递公司　　快递单号　　通过页面接受过来
    logi_company = request.data.get("refund[0][logi_company]", "")
    logi_sid = request.data.get("refund[0][logi_sid]", "")

    # 如果num　等与０ break
    if num == 0:  # 提交的退款产品数量为0
        return
    # １、判断能否退款　能则继续　否则 break
    if categry == 0:
        print "退款。。。。。"
        if judge_Refund(order_id=oid):
            # ２、get_or_create 退款单对象
            trade, order, order_count = get_Refund_Order_Trade(order_id=oid)
            # 退款处理　生成退款单
            sale_refund, state = create_Sale_Refund(trade_id=trade.id, order_id=order.id)
            # 如果state 为真　则继续
            if state:
                print "state is here: ", state
                # 修改该订单的
                order.refund_id = sale_refund.id  # refund_id
                # refund_fee    = models.FloatField(default=0.0,verbose_name=u'退款费用')
                # 退款费用为原来订单的实付款除以数量的单价　乘以要退产品的数量
                order.refund_fee = order.payment / order.num * num
                # refund_status =  SaleRefund.REFUND_WAIT_SELLER_AGREE 已经申请退款状态
                order.refund_status = SaleRefund.REFUND_WAIT_SELLER_AGREE
                order.save()
                # 保存其他信息到sale_refund
                save_Other_Atriibut(trade=trade, order=order, sale_refund=sale_refund, refund_num=num,
                                    reason=reason)
            # 否则
            else:
                # 返回提示已经申请　禁止重复申请
                return {"res": "already_refund"}
                # (有记录则曾经申请过　不予再次申请)
        else:
            return {"res": "forbidden"}
    if categry:
        print "退货。。。。。"
        if judge_Refund_Product(order_id=oid):
            # ２、get_or_create 退款单对象
            trade, order, order_count = get_Refund_Order_Trade(order_id=oid)
            # 退款处理　生成退款单
            sale_refund, state = create_Sale_Refund(trade_id=trade.id, order_id=order.id)
            # 如果state 为真　则继续
            if state:
                print "state is here: ", state
                # 修改该订单的
                order.refund_id = sale_refund.id  # refund_id
                # refund_fee    = models.FloatField(default=0.0,verbose_name=u'退款费用')
                # 退款费用为原来订单的实付款除以数量的单价　乘以要退产品的数量
                order.refund_fee = order.payment / order.num * num
                # refund_status =  SaleRefund.REFUND_WAIT_SELLER_AGREE 已经申请退款状态
                order.refund_status = SaleRefund.REFUND_WAIT_SELLER_AGREE
                order.save()
                # 保存其他信息到sale_refund
                save_Other_Atriibut(trade=trade, order=order, sale_refund=sale_refund, refund_num=num,
                                    reason=reason)
                # sale_refund good_status 的商品状态为买家收到货 BUYER_RETURNED_GOODS,'买家已退货'
                # ??
                sale_refund.good_status = SaleRefund.BUYER_RETURNED_GOODS
                # 填写物流信息后 表明买家已经退货
                # 这里最好指定 有哪些物流公司 然后根据物流公司接口查询物流单号是否已经有退货的物流信息  有则予以退货申请
                # 否则 返回未查到物流信息
                sale_refund.save()

                # 如果物流信息不是空　，　填写物流信息
                if logi_company and logi_sid:
                    save_Resund_Product_Atribut(refund=sale_refund, company=logi_company, sid=logi_sid)
            # 否则
            else:
                # 返回提示已经申请　禁止重复申请
                return {"res": "already_refund"}
                # (有记录则曾经申请过　不予再次申请)
        else:
            return {"res": "forbidden"}
    return {"res": "refund_success"}


def refund_Handler(request):
    reason = int(request.data.get("refund[0][reason]", "0"))
    refund_or_pro = int(request.data["refund[0][refund_or_pro]"])  # 用来判断是退货还是退款的变量
    if refund_or_pro == 0:  # 退款处理
        print "退款。。。"
        message = sub_Handler(request=request, reason=reason, categry=refund_or_pro)
        return message
    if refund_or_pro == 1:  # 退货处理
        print "退货。。。"
        message = sub_Handler(request=request, reason=reason, categry=refund_or_pro)
        return message


"""
检查订单状态  如果子订单sale_order 的refund_id 中的数量 等于订单中的数量 表示order都已经退单 并且这个退款单是成功的状态 则将这笔sale_order关闭
如果这笔Trade 的order 都是退款关闭 则 将 这笔Trade关闭
"""