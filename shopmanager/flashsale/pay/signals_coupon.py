# coding=utf-8
from flashsale.pay.models import SaleTrade, SaleOrder, SaleRefund
from flashsale.pay.models_user import Customer
from models_coupon import IntegralLog, Integral
from django.db.models.signals import post_save
import logging
import datetime
from django.db.models import ObjectDoesNotExist
from flashsale.pay.models_coupon_new import UserCoupon, CouponTemplate

from django.db.models import F
from common.modelutils import update_model_fields
from shopback.base import log_action, CHANGE


"""
当创建订单的时候创建积分待确认记录
"""
INTEGRAL_START_TIME = datetime.datetime(2015, 7, 25, 0, 0, 0)
logger = logging.getLogger('django.request')


def get_IntegralLog(buyer_id, orid):
    try:
        integrallog = IntegralLog.objects.get(integral_user=buyer_id, order_id=orid)
        return integrallog
    except ObjectDoesNotExist:
        return False


def add_Order_Integral(sender, instance, created, **kwargs):
    # 记录要对应到商品上
    # 根据订单的状态来处理积分的状态
    order_created = instance.created  # Order创建时间
    order_id = instance.id
    pic_link = instance.pic_path
    trade_id = instance.sale_trade_id
    order_status = instance.status
    order_content = '[{"order_id":"%s","pic_link":"%s","trade_id":"%s","order_status":"%s"}]' % (
        str(order_id), str(pic_link), str(trade_id), str(order_status))
    trade = SaleTrade.objects.get(id=instance.sale_trade_id)  # 由订单找交易
    cus = Customer.objects.get(id=trade.buyer_id)  # 由交易的buyer_id找
    buyer_id = trade.buyer_id  # 用户ID
    orid = instance.id  # order id
    if instance.outer_id == 'RMB100' or instance.outer_id == 'RMB118' or instance.outer_id == 'RMB125':  # 代理费不需要生成积分
        return
    if order_created >= INTEGRAL_START_TIME and instance.status == SaleOrder.WAIT_SELLER_SEND_GOODS:
        # 生成时间必须是大于活动开始时间  AND  必须是已经付款的才有积分记录   # SaleOrder.WAIT_SELLER_SEND_GOODS  # 已经付款
        integrallog = get_IntegralLog(buyer_id, orid)
        if integrallog is False:
            integrallog = IntegralLog()
            integrallog.integral_user = buyer_id
            integrallog.order_id = orid
            integrallog.mobile = cus.mobile
            integrallog.log_value = int(instance.payment)
            integrallog.order = order_content
            integrallog.log_status = IntegralLog.PENDING
            integrallog.log_type = IntegralLog.ORDER_INTEGRA
            integrallog.in_out = IntegralLog.LOG_IN
            integrallog.save()
        else:
            integrallog.mobile = cus.mobile
            integrallog.log_value = int(instance.payment)
            integrallog.order = order_content
            integrallog.log_status = IntegralLog.PENDING
            integrallog.log_type = IntegralLog.ORDER_INTEGRA
            integrallog.in_out = IntegralLog.LOG_IN
            integrallog.save()
    elif instance.status == SaleOrder.TRADE_CLOSED and order_created >= INTEGRAL_START_TIME:
        # TRADE_CLOSED # 根据订单的状态来处理积分的状态  退款关闭的 积分要取消掉
        integrallog = get_IntegralLog(buyer_id, orid)
        if integrallog:
            integrallog.log_status = IntegralLog.CANCEL  # 取消积分
            integrallog.save()
    elif instance.status == SaleOrder.TRADE_FINISHED and order_created >= INTEGRAL_START_TIME:
        # 交易成功  # 修改积分状态为确认状态
        # 没有就创建  有则修改  该用户的积分累计记录
        integrallog = get_IntegralLog(buyer_id, orid)
        if integrallog:
            integrallog.log_status = IntegralLog.CONFIRM  # 确认积分
            integrallog.save()
            try:
                user_interal = Integral.objects.get(integral_user=buyer_id)
                user_interal.integral_value += int(instance.payment)
                user_interal.save()
            except ObjectDoesNotExist:
                user_interal = Integral()
                user_interal.integral_user = buyer_id
                user_interal.integral_value = int(instance.payment)
                user_interal.save()


post_save.connect(add_Order_Integral, sender=SaleOrder)


def xlmm_Recharge(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.models import CarryLog, XiaoluMama

    order_id = instance.id
    payment = instance.payment
    systemoa = 641  # 系统操作的id 641
    if instance.sku_id == '':
        instance.sku_id = 0
    sku_id = int(instance.sku_id)  # 上架商品的id

    # 上架商品的id 注意在服务器上要修改
    sku_id_100_10 = 86345
    sku_id_200_30 = 86346
    sku_id_500_100 = 86347

    payment_value = 0

    SKU_IDS = {sku_id_100_10: 10, sku_id_200_30: 30, sku_id_500_100: 100}

    if sku_id not in SKU_IDS.keys():
        return  # 不是充值商品不处理
    if instance.status != SaleOrder.WAIT_SELLER_SEND_GOODS:
        return  # 不是已经付款不处理
    if instance.refund_status != SaleRefund.NO_REFUND:
        return  # 有退款操作不处理
    # 计算　附加值
    if sku_id == sku_id_100_10:
        payment_value = (payment + SKU_IDS[sku_id_100_10]) * 100  # 充值100送10元
    elif sku_id == sku_id_200_30:
        payment_value = (payment + SKU_IDS[sku_id_200_30]) * 100  # 充值200送30
    elif sku_id == sku_id_500_100:
        payment_value = (payment + SKU_IDS[sku_id_500_100]) * 100  # 充值500送100

    sale_trade = instance.sale_trade  # 交易
    buyer_id = sale_trade.buyer_id  # 客户id
    customer = Customer.objects.get(id=buyer_id)

    try:
        xlmm = XiaoluMama.objects.get(openid=customer.unionid, charge_status=XiaoluMama.CHARGED)
    except XiaoluMama.DoesNotExist:
        return  # 没有找到代理　不做处理 没有接管处理
    # 捕捉已付款　　判断carrylog中的记录是否存在　　
    try:
        clog = CarryLog.objects.get(xlmm=xlmm.id, order_num=order_id, log_type=CarryLog.RECHARGE,
                                    carry_type=CarryLog.CARRY_IN)
        return  # 存在　则不做处理
    except CarryLog.DoesNotExist:
        # 创建钱包记录
        CarryLog.objects.create(xlmm=xlmm.id, order_num=order_id, buyer_nick=xlmm.weikefu,
                                value=payment_value, log_type=CarryLog.RECHARGE,
                                carry_type=CarryLog.CARRY_IN, status=CarryLog.CONFIRMED)
        # 修改xlmm　cash
        before_cash = xlmm.cash
        xlmm.cash = F('cash') + payment_value
        update_model_fields(xlmm, update_fields=['cash'])
        action_desc = u"代理充值修改cash:{0}金额{1}".format(before_cash, xlmm.cash)
        log_action(systemoa, xlmm, CHANGE, action_desc)

        # 修改xlmm lowest_uncoushout
        before_lowest_uncoushout = xlmm.lowest_uncoushout
        xlmm.lowest_uncoushout = F('lowest_uncoushout') + payment_value / 100.0
        update_model_fields(xlmm, update_fields=['lowest_uncoushout'])
        action_desc_lowest = u"代理充值修改lowest_uncoushout:{0}金额{1}".format(before_lowest_uncoushout,
                                                                        xlmm.lowest_uncoushout)
        log_action(systemoa, xlmm, CHANGE, action_desc_lowest)

        # 交易状态修改　交易成功
        instance.status = SaleOrder.TRADE_FINISHED
        update_model_fields(instance, update_fields=['status'])
        log_action(systemoa, instance, CHANGE, u"充值修改该订单明细状态")
        instance.sale_trade.status = SaleTrade.TRADE_FINISHED
        update_model_fields(instance.sale_trade, update_fields=['status'])
        log_action(systemoa, instance.sale_trade, CHANGE, u"充值修改该订单交易状态")


post_save.connect(xlmm_Recharge, sender=SaleOrder)

from flashsale.pay.signals import signal_saletrade_pay_confirm, signal_saletrade_refund_post


def release_Coupon_Buy_Way(sender, obj, **kwargs):
    """
    更具优惠券模板中有效且是购买发放模式的模板　
    判断当前时间是否是在　模板定义的预置时间到结束时间
    如果是在该时间内　则发放对应的优惠券
    """
    order = obj.sale_orders.all()[0] if obj.sale_orders.exists() else False  # 这里充值的交易只有一个订单
    if order and order.item_id in ['22030', '14362', '2731']:  # 列表中填写 充值产品id
        return  # 如果是充值产品 则不发放优惠券

    now = datetime.datetime.now()
    tpls = CouponTemplate.objects.filter(valid=True, way_type=CouponTemplate.BUY_WAY)  # 有效的并且是购买方式发放的优惠券模板
    tpls = tpls.exclude(type=CouponTemplate.NEW_YEAR)  # 排除特殊条件的优惠券
    tpls = tpls.filter(release_start_time__lte=now, release_end_time__gte=now)  # 在发放时间内的模板

    for tpl in tpls:
        # 在允许发送情况下　准备发放优惠券
        # 获取该用户的该模板的优惠券
        coups = UserCoupon.objects.filter(customer=obj.buyer_id, cp_id__template__id=tpl.id)
        free_coupons = coups.filter(status=UserCoupon.FREEZE)
        if free_coupons.exists():
            one_freeze_coupon = free_coupons[0]
            one_freeze_coupon.status = UserCoupon.UNUSED  # 从冻结状态 改为 未使用
            one_freeze_coupon.sale_trade = obj.id  # 绑定当前的交易id
            one_freeze_coupon.save()
            break  # 如果该用户存在冻结的该模板类型优惠券　则将该优惠券解冻并退出所有模板发放（一次购买仅解冻一个优惠券或发放一次该优惠券）
        # 发放优惠券
        try:
            trade_id = obj.id  # 交易id
            buyer_id = obj.buyer_id  # 用户
            kwargs = {"trade_id": trade_id, "buyer_id": buyer_id, "template_id": tpl.id}
            if obj.payment >= tpl.release_fee:  # 消费费用大于模板定义费用则发放
                coupon = UserCoupon()
                coupon.release_by_template(**kwargs)
        except Exception, exc:
            logger.error(exc.message, exc_info=True)


signal_saletrade_pay_confirm.connect(release_Coupon_Buy_Way, sender=SaleTrade)


def freeze_coupon_by_refund(sender, obj, **kwargs):
    # 退款信号
    if obj.trade_id:
        coup = UserCoupon.objects.filter(sale_trade=obj.trade_id)
        # 存在则将优惠券状态 该为 冻结
        coup.update(status=UserCoupon.FREEZE)


signal_saletrade_refund_post.connect(freeze_coupon_by_refund, sender=SaleRefund)