# coding=utf-8
import datetime
import logging
from core.options import log_action, ADDITION, CHANGE
from rest_framework import exceptions
from common.modelutils import update_model_fields
from flashsale.pay.models import SaleOrder
from flashsale.pay.models import SaleRefund, Customer
from flashsale.pay import tasks
from shopback.trades.models import PackageSkuItem

logger = logging.getLogger(__name__)


def modify_refund_fee(customer, order, refund, refund_fee,
                      good_status=None, reason=None, desc=None, num=None):
    refund_update_fields = []
    refund_params = {
        "reason": reason,
        "refund_num": num,
        "good_status": good_status,
        "desc": desc,
        "status": SaleRefund.REFUND_WAIT_SELLER_AGREE,  # 修改之后重置为申请状态
    }
    for k, v in refund_params.iteritems():
        if v is None:
            continue
        if hasattr(refund, k) and getattr(order, k) != v:
            setattr(refund, k, v)
            refund_update_fields.append(k)
    if refund_update_fields:
        update_model_fields(refund, update_fields=refund_update_fields)
        log_action(customer, refund, CHANGE, u'用户售后被拒绝后修改order信息！')
        tasks.pushTradeRefundTask.delay(refund.id)

    # 修改该订单的
    order_params = {
        "refund_id": refund.id,
        "refund_fee": refund_fee,
        "refund_status": SaleRefund.REFUND_WAIT_SELLER_AGREE
    }
    order_update_fields = []
    for k, v in order_params.iteritems():
        if hasattr(order, k) and getattr(order, k) != v:
            setattr(order, k, v)
            order_update_fields.append(k)
    if order_update_fields:
        order.save(update_fields=order_update_fields)
        log_action(customer, order, CHANGE, u'用户售后修改退款单修改order信息！')


def modify_logistic_refund(customer, company, order, sid, refund):
    order.refund_status = SaleRefund.REFUND_CONFIRM_GOODS
    order.save(update_fields=['refund_status'])
    log_action(customer, order, CHANGE, u'用户退货填写物流信息,修改order　refund_status 到买家退货状态！')

    refund.company_name = company
    refund.sid = sid
    refund.status = SaleRefund.REFUND_CONFIRM_GOODS  # 修改到买家已经退货状态(退货途中)
    refund.good_status = SaleRefund.BUYER_RETURNED_GOODS  # 修改商品状态到买家已经退货
    update_model_fields(refund, update_fields=['company_name', 'sid', 'status', 'good_status'])
    log_action(customer, refund, CHANGE, u'用户退货填写物流信息！')


def refund_Handler(request):
    try:
        content = request.POST
        modify = int(content.get("modify", 0))
        company = content.get("company", '')
        sid = content.get("sid", '')
        oid = int(content.get("id", 0))
        reason = int(request.data.get("reason", "0"))
        num = int(request.data.get("num", 0))
        refund_channel = request.data.get("refund_channel", "")
        desc = request.data.get("description", '')
        proof_pic = str(request.data.get("proof_pic", ""))
        order = SaleOrder.objects.filter(id=oid).first()  # 获取订单
        user = request.user.id
        customer = Customer.objects.filter(user=user, status=Customer.NORMAL).first()
        if not customer:
            return {"code": 7, "info": "用户状态异常!", "apply_fee": 0}
        if not order:
            return {"code": 3, "info": "订单没有找到!", "apply_fee": 0}
        if order.second_kill_title():
            return {"code": 4, "info": "秒杀商品暂不支持退单，请见谅!", "apply_fee": 0}

        pfcl = []
        if proof_pic != "":
            pfcl = proof_pic.split(',')
        proof_p = pfcl
        if order.status == SaleOrder.WAIT_SELLER_SEND_GOODS:  # 已经付款
            good_status = SaleRefund.BUYER_NOT_RECEIVED
        elif order.status == SaleOrder.TRADE_BUYER_SIGNED:  # 确认签收
            good_status = SaleRefund.BUYER_RECEIVED
        else:  # 已经付款　或者　确认签收 才允许退款
            return {"code": 6, "info": "请签收后申请退款!", "apply_fee": 0}
        refund_fee = order.calculate_refund_fee(num)
        refund = SaleRefund.objects.filter(id=order.refund_id).first()
        if modify == 1:  # 修改该金额
            if not refund:
                return {"code": 4, "info": "退款单不存在!", "apply_fee": 0}
            if refund.status in (
                    SaleRefund.REFUND_SUCCESS, SaleRefund.REFUND_WAIT_RETURN_GOODS,
                    SaleRefund.REFUND_APPROVE, SaleRefund.REFUND_CLOSED):  # 退款成功 等待返款 同意退款 退款关闭  之后不允许修改
                return {"code": 5, "info": "退款单状态不予修改!", "apply_fee": 0}
            modify_refund_fee(user, order, refund, refund_fee,
                              good_status=good_status, reason=None, desc=None, num=None)
            return {"code": 0, "info": "退款单修改成功!", "apply_fee": refund_fee}

        elif modify == 2:  # 修改退款单的物流信息
            if refund.status in (SaleRefund.REFUND_SUCCESS, SaleRefund.REFUND_APPROVE, SaleRefund.REFUND_CLOSED):
                # 退款成功 等待返款 退款关闭  之后不允许修改 物流信息
                return {"code": 0, "info": "当前状态不予修改物流信息!", "apply_fee": refund_fee}
            modify_logistic_refund(user, company, order, sid, refund)
            return {"code": 0, "info": "修改物流成功!", "apply_fee": refund_fee}
        elif modify == 3:  # 修改数量返回退款金额(不做数据库写动作)
            return {"code": 0, "info": "获取可退金额成功!", "apply_fee": refund_fee}

        # 已经付款状态下　判断　订货后　不予退款
        if order.status == SaleOrder.WAIT_SELLER_SEND_GOODS:
            psi = PackageSkuItem.objects.filter(oid=order.oid).first()
            if psi and psi.is_booked():
                return {"code": 9,
                        "info":
                            "您的订单已发送至厂家订货，工厂正在发货中。若要取消订单，请在收货后选择七天无理由退货。若有其他问题，请联系客服400-8235-355。",
                        "apply_fee": 0}

        # 创建退款单
        if refund:
            return {"code": 8, "info": "申请已经提交!", "apply_fee": refund_fee}
        if int(reason) == 10 and order.status == SaleOrder.TRADE_BUYER_SIGNED:
            # 如果是七天无理由退货　判定是否是签收后　七天以内
            now = datetime.datetime.now()
            d = (now - order.sign_time).days
            if d > 7:
                return {"code": 10, "info": "您的订单已经超过七天,请选择重选原因申请", "apply_fee": 0}

        if num == 0 or None:  # 提交的退款产品数量为0
            raise exceptions.APIException(u'退货数量为0')
        if num > order.num:
            raise exceptions.APIException(u'退货数量超过购买数量')
        # 退款处理　生成退款单
        if refund_fee > (order.payment / order.num) * num:  # 退款金额不能大于 单价乘以退款数量
            raise exceptions.APIException(u'退货金额大于实付款')
        refund = order.refund
        if not refund:
            refund = order.do_refund(reason=reason, refund_num=num, refund_fee=refund_fee,
                                     good_status=good_status,
                                     desc=desc, refund_channel=refund_channel, proof_pic=proof_p)
            refund.agree_return_goods()  # 处理　同意申请
            log_action(user, refund, ADDITION, u'用户售后增加退货款单信息！')
        tasks.pushTradeRefundTask.delay(refund.id)

        return {"code": 0, "info": "操作成功", "res": "ok"}
    except Exception, exc:
        logger.error(u'refund_Handler %s' % exc, exc_info=True)
        return {"code": 1, "info": exc.message, "apply_fee": 0}
