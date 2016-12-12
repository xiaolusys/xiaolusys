# coding=utf-8
from __future__ import unicode_literals, absolute_import
import datetime
from django.db import IntegrityError
from django.db import transaction
from core.options import log_action, CHANGE

from rest_framework import exceptions
from ...models.transfer_coupon import CouponTransferRecord
from ...models.usercoupon import UserCoupon
import logging

logger = logging.getLogger(__name__)
from .usercoupon import get_user_coupons_by_ids, freeze_transfer_coupon, get_freeze_boutique_coupons_by_transfer, \
    rollback_user_coupon_status_2_unused_by_ids
from flashsale.pay.apis.v1.customer import get_customer_by_django_user
from flashsale.pay.models import BudgetLog

__ALL__ = [
    'create_coupon_transfer_record',
    'get_transfer_record_by_id',
]


def get_elite_score_by_templateid(templateid, mama):
    # type: (int, XiaoluMama) -> Tuple[int, int, float]
    """通过优惠券模板ID　和　小鹿妈妈 获取　精品券商品id　积分　和　价格
    """
    from flashsale.pay.models.product import ModelProduct

    virtual_model_products = ModelProduct.objects.get_virtual_modelproducts()  # 虚拟商品
    find_mp = None
    for md in virtual_model_products:
        md_bind_tpl_id = md.extras.get('template_id')
        if not md_bind_tpl_id:
            continue
        if templateid == md_bind_tpl_id:
            find_mp = md
            break
    if find_mp:
        if not mama:
            return find_mp.products[0].id, find_mp.products[0].elite_score, find_mp.products[0].agent_price
        else:
            for product in find_mp.products:
                if mama.elite_level in product.name:
                    return product.id, product.elite_score, product.agent_price
    return 0, 0, 0.0


def get_transfer_record_by_id(id):
    # type: (int) -> CouponTransferRecord
    return CouponTransferRecord.objects.get(id=id)


def create_present_coupon_transfer_record(customer, template, coupon_id, uni_key_prefix=None):
    # type: (Customer, CouponTemplate, int, Optional[int]) -> CouponTransferRecord
    """创建赠送优惠券流通记录
    """
    to_mama = customer.get_charged_mama()
    to_mama_nick = customer.nick
    to_mama_thumbnail = customer.thumbnail

    coupon_to_mama_id = to_mama.id
    init_from_mama_id = to_mama.id

    coupon_from_mama_id = 0
    from_mama_thumbnail = 'http://7xogkj.com2.z0.glb.qiniucdn.com/222-ohmydeer.png?imageMogr2/thumbnail/60/format/png'
    from_mama_nick = 'SYSTEM'

    transfer_type = CouponTransferRecord.IN_GIFT_COUPON
    date_field = datetime.date.today()
    transfer_status = CouponTransferRecord.DELIVERED
    uni_key_prefix = 'gift-%s' % uni_key_prefix if uni_key_prefix else 'gift'
    uni_key = "%s-%s-%s" % (uni_key_prefix, to_mama.id, coupon_id)
    order_no = 'gift-%s' % coupon_id
    coupon_value = int(template.value)
    product_img = template.extras.get("product_img") or ''

    try:
        coupon = CouponTransferRecord(coupon_from_mama_id=coupon_from_mama_id,
                                      from_mama_thumbnail=from_mama_thumbnail,
                                      from_mama_nick=from_mama_nick,
                                      coupon_to_mama_id=coupon_to_mama_id,
                                      to_mama_thumbnail=to_mama_thumbnail,
                                      to_mama_nick=to_mama_nick,
                                      coupon_value=coupon_value,
                                      init_from_mama_id=init_from_mama_id,
                                      order_no=order_no,
                                      template_id=template.id,
                                      product_img=product_img,
                                      coupon_num=1,
                                      transfer_type=transfer_type,
                                      uni_key=uni_key,
                                      date_field=date_field,
                                      transfer_status=transfer_status)
        coupon.save()
        return coupon
    except Exception as e:
        return e


def send_order_transfer_coupons(customer_id, order_id, order_oid, order_num, product_id):
    # type: (int, int, text_type, int, int) -> None
    from ...tasks import task_send_transfer_coupons

    task_send_transfer_coupons.delay(customer_id, order_id, order_oid, order_num, product_id)


@transaction.atomic
def coupon_exchange_saleorder(customer, order_id, mama_id, exchg_template_id, coupon_num):
    logger.info({
        'message': u'exchange order:customer=%s, mama_id=%s coupon_num=%s order_id=%s templateid=%s' % (
            customer.id, mama_id, coupon_num, order_id, exchg_template_id),
    })

    # (1)sale order置为已经兑换
    from flashsale.pay.models.trade import SaleOrder, SaleTrade

    sale_order = SaleOrder.objects.filter(oid=order_id).first()
    if sale_order:
        if sale_order.status < SaleOrder.WAIT_BUYER_CONFIRM_GOODS:
            logger.warn({
                'message': u'exchange order: order_id=%s status=%s' % (order_id, sale_order.status),
            })
            raise exceptions.ValidationError(u'订单记录状态不对，兑换失败!')
        if sale_order and sale_order.extras.has_key('exchange') and sale_order.extras['exchange'] == True:
            logger.warn({
                'message': u'exchange order: order_id=%s has already exchg' % (order_id),
            })
            raise exceptions.ValidationError(u'订单已经被兑换过了，兑换失败!')
        sale_order.extras['exchange'] = True
        SaleOrder.objects.filter(oid=order_id).update(extras=sale_order.extras)
    else:
        logger.warn({
            'message': u'exchange order: order_id=%s not exist' % (order_id),
        })
        raise exceptions.ValidationError(u'找不到订单记录，兑换失败!')

    # (2)用户优惠券需要变成使用状态
    user_coupons = UserCoupon.objects.filter(customer_id=customer.id, template_id=int(exchg_template_id),
                                             status=UserCoupon.UNUSED)
    use_num = 0
    for coupon in user_coupons:
        if use_num < int(coupon_num):
            UserCoupon.objects.filter(uniq_id=coupon.uniq_id).update(status=UserCoupon.USED, trade_tid=sale_order.oid,
                                                                     finished_time=datetime.datetime.now())
            use_num += 1
        else:
            break

    # (3)在user钱包写收入记录
    from flashsale.pay.models.user import BudgetLog

    today = datetime.date.today()
    order_log = BudgetLog(customer_id=customer.id, flow_amount=round(sale_order.payment * 100),
                          budget_type=BudgetLog.BUDGET_IN,
                          budget_log_type=BudgetLog.BG_EXCHG_ORDER, referal_id=sale_order.id,
                          uni_key=sale_order.oid, status=BudgetLog.CONFIRMED,
                          budget_date=today)

    order_log.save()

    # (4)在精品券流通记录增加兑换记录
    res = CouponTransferRecord.create_exchg_order_record(customer, int(coupon_num), sale_order,
                                                         int(exchg_template_id))

    return res


@transaction.atomic
def saleorder_return_coupon_exchange(salerefund, payment):
    logger.info({
        'message': u'return exchange order:customer=%s, payment=%s refundid=%s' % (
            salerefund.buyer_id, payment, salerefund.id),
    })

    # 判断这个退款单对应的订单是曾经兑换过的
    from flashsale.pay.models.trade import SaleOrder
    sale_order = SaleOrder.objects.filter(id=salerefund.order_id).first()
    if not (sale_order and sale_order.extras.has_key('exchange') and sale_order.extras['exchange'] == True):
        res = {}
        return res

    # 找出兑换这个订单的xlmm
    from flashsale.xiaolumm.models import XiaoluMama
    from flashsale.coupon.models.transfer_coupon import CouponTransferRecord
    cts = CouponTransferRecord.objects.filter(transfer_type=CouponTransferRecord.OUT_EXCHG_SALEORDER,
                                              uni_key=sale_order.oid, transfer_status=CouponTransferRecord.DELIVERED).first()
    if cts:
        mama_id = cts.coupon_from_mama_id
        mama = XiaoluMama.objects.filter(id=mama_id).first()
    else:
        logger.error({
            'message': u'return exchange order:CouponTransferRecord not found, customer=%s, payment=%s order oid=%s' % (
                salerefund.buyer_id, payment, sale_order.oid),
        })
        res = {}
        return res

    from flashsale.pay.models.user import UserBudget, Customer
    not_enough_budget = False
    customer = Customer.objects.normal_customer.filter(unionid=mama.openid).first()
    user_budgets = UserBudget.objects.filter(user=customer)
    if user_budgets.exists():
        user_budget = user_budgets[0]
        if user_budget.budget_cash < int(payment):
            not_enough_budget = True

    # (1)在user钱包写支出记录，支出不够变成负数
    from flashsale.pay.models.user import BudgetLog
    today = datetime.date.today()
    order_log = BudgetLog(customer_id=customer.id, flow_amount=int(payment),
                          budget_type=BudgetLog.BUDGET_OUT,
                          budget_log_type=BudgetLog.BG_EXCHG_ORDER, referal_id=salerefund.id,
                          uni_key=salerefund.refund_no, status=BudgetLog.CONFIRMED,
                          budget_date=today)

    order_log.save()

    # (2)sale order置为已经取消兑换
    if sale_order:
        sale_order.extras['exchange'] = False
        SaleOrder.objects.filter(id=salerefund.order_id).update(extras=sale_order.extras)
    else:
        logger.warn({
            'message': u'return exchange order: order_id=%s not exist' % (salerefund.order_id),
        })
        raise exceptions.ValidationError(u'找不到订单记录，取消兑换失败!')

    # (3)用户优惠券需要变成未使用状态,如果零钱不够扣则变为冻结,优惠券扣除张数等于退款金额除商品价格；有可能买了多件商品，只退部分，那么
    # 只能修改部分优惠券的状态
    user_coupon = UserCoupon.objects.filter(trade_tid=sale_order.oid,
                                            status=UserCoupon.USED)
    return_coupon_num = round(payment / sale_order.price)
    if user_coupon.count() < return_coupon_num:
        logger.warn({
            'message': u'return exchange order: user_coupon.count() %s < return_coupon_num %s' % (
                user_coupon.count(), return_coupon_num),
        })
    num = 0
    for coupon in user_coupon:
        if num >= return_coupon_num:
            break
        else:
            num += 1
        if not not_enough_budget:
            UserCoupon.objects.filter(uniq_id=coupon.uniq_id).update(status=UserCoupon.UNUSED, trade_tid='',
                                                                     finished_time=datetime.datetime.now())
        else:
            UserCoupon.objects.filter(uniq_id=coupon.uniq_id).update(status=UserCoupon.FREEZE, trade_tid='',
                                                                     finished_time=datetime.datetime.now())

    # (4)在精品券流通记录增加退货退券记录
    logger.info({
        'message': u'exchange order:return_coupon_num=%s ' % (return_coupon_num),
    })
    res = CouponTransferRecord.gen_return_record(customer, return_coupon_num,
                                                 int(user_coupon.template_id), sale_order.sale_trade.tid)

    return res


@transaction.atomic()
def apply_pending_return_transfer_coupon(coupon_ids, customer):
    # type: (List[int]) -> bool
    """下属 提交待审核　退精品券　给　上级
    """
    from .coupontemplate import get_coupon_template_by_id
    from flashsale.xiaolumm.apis.v1.xiaolumama import get_mama_by_id
    coupons = get_user_coupons_by_ids(coupon_ids)
    mama = customer.get_xiaolumm()
    template_ids = set()
    upper_mamas = {}
    for coupon in coupons:
        if not coupon.can_return_upper_mama():
            raise Exception('%s不支持退券给上级妈妈' % coupon.title)
        template_ids.add(coupon.template_id)

        # 组织下 数据  key是上级妈妈id  value是 要退给上级妈妈的券 数量
        chain = coupon.return_mama_chain
        upmm = chain[-1]
        if upmm not in upper_mamas:
            upper_mamas[upmm] = 1
        else:
            upper_mamas[upmm] += 1
    if len(template_ids) != 1:
        raise Exception('多种券不支持同时退券')

    template_id = template_ids.pop()
    template = get_coupon_template_by_id(template_id)
    product_id, elite_score, agent_price = get_elite_score_by_templateid(template_id, mama)
    coupon_value = int(template.value)
    product_img = template.extras.get("product_img") or ''

    for upper_mama_id, num in upper_mamas.iteritems():
        # 生成 带审核 流通记录
        total_elite_score = elite_score * num
        count = CouponTransferRecord.objects.filter(transfer_type=CouponTransferRecord.IN_RETURN_COUPON,
                                                    uni_key__contains='return-upper-%s-%s-' % (
                                                        upper_mama_id, template.id)).count()
        uni_key = 'return-upper-%s-%s-%s' % (upper_mama_id, template.id, count + 1)
        upper_mm = get_mama_by_id(upper_mama_id)  # 要退给上级的妈妈
        upper_customer = upper_mm.get_customer()
        new_transfer = CouponTransferRecord(
            coupon_from_mama_id=mama.id,
            from_mama_thumbnail=customer.thumbnail,
            from_mama_nick=customer.nick,
            coupon_to_mama_id=upper_mama_id,
            to_mama_thumbnail=upper_customer.thumbnail,
            to_mama_nick=upper_customer.nick,
            coupon_value=coupon_value,
            template_id=template_id,
            order_no=uni_key,
            product_img=product_img,
            coupon_num=num,
            transfer_type=CouponTransferRecord.IN_RETURN_COUPON,
            uni_key=uni_key,
            date_field=datetime.date.today(),
            product_id=product_id,
            elite_score=total_elite_score,
            transfer_status=CouponTransferRecord.PENDING)
        new_transfer.save()
        freeze_transfer_coupon(coupon_ids, new_transfer.id)  # 冻结优惠券
    return True


@transaction.atomic()
def apply_pending_return_transfer_coupon_2_sys(coupon_ids, customer):
    # type: (List[int], Customer) -> float
    """退精品券给系统　生成退券给系统记录
    """
    from .coupontemplate import get_coupon_template_by_id
    from flashsale.pay.models import BudgetLog

    coupons = get_user_coupons_by_ids(coupon_ids)
    mama = customer.get_xiaolumm()
    template_ids = set()
    for coupon in coupons:
        if not coupon.can_return_sys():
            raise Exception('%s不支持退券给系统' % coupon.title)
        template_ids.add(coupon.template_id)
    if len(template_ids) != 1:
        raise Exception('多种券不支持同时退券')
    template_id = template_ids.pop()
    template = get_coupon_template_by_id(template_id)
    product_id, elite_score, agent_price = get_elite_score_by_templateid(template_id, mama)
    product_img = template.extras.get("product_img") or ''
    coupon_value = int(template.value)
    num = coupons.count()
    total_elite_score = elite_score * num  # 计算总积分
    total_agent_price = agent_price * num  # 计算总退款
    count = CouponTransferRecord.objects.get_out_cash_transfer_coupons().filter(coupon_from_mama_id=mama.id).count()
    uni_key = 'return-sys-%s-%s' % (mama.id, count)
    transfer = CouponTransferRecord(
        coupon_from_mama_id=mama.id,
        from_mama_thumbnail=customer.thumbnail,
        from_mama_nick=customer.nick,
        coupon_to_mama_id=0,
        to_mama_thumbnail='http://7xogkj.com2.z0.glb.qiniucdn.com/222-ohmydeer.png?imageMogr2/thumbnail/60/format/png',
        to_mama_nick='SYSTEM',
        coupon_value=coupon_value,
        template_id=template_id,
        order_no='return-money-%s' % total_agent_price,
        product_img=product_img,
        coupon_num=num,
        transfer_type=CouponTransferRecord.OUT_CASHOUT,
        uni_key=uni_key,
        date_field=datetime.date.today(),
        product_id=product_id,
        elite_score=total_elite_score,
        transfer_status=CouponTransferRecord.PENDING)
    transfer.save()
    BudgetLog.create_return_coupon_log(customer.id, transfer.id, flow_amount=int(total_agent_price * 100))  # 生成钱包待确定记录
    freeze_transfer_coupon(coupon_ids, transfer.id)  # 冻结优惠券
    return True


@transaction.atomic()
def agree_apply_transfer_record(user, transfer_record_id):
    # type: (DjangoUser, int) -> bool
    """同意下属退还　的流通记录　　
    1. 将流通记录设置为待发放　　
    """
    from flashsale.xiaolumm.tasks.tasks_mama_dailystats import task_calc_xlmm_elite_score

    customer = get_customer_by_django_user(user)
    record = get_transfer_record_by_id(transfer_record_id)
    if record.transfer_type != CouponTransferRecord.IN_RETURN_COUPON:
        raise Exception('记录类型有错')
    if record.transfer_status != CouponTransferRecord.PENDING:
        raise Exception('记录状态不在待审核')
    mama = customer.get_xiaolumm()
    if record.coupon_to_mama_id != mama.id:
        raise Exception('记录审核人错误')
    record.transfer_status = CouponTransferRecord.PROCESSED  # 待发放状态
    record.save(update_fields=['transfer_status', 'modified'])
    task_calc_xlmm_elite_score(mama.id)  # 重算积分
    return True


@transaction.atomic()
def reject_apply_transfer_record(user, transfer_record_id):
    # type: (DjangoUser, int) -> bool
    """拒绝下属退还　的流通记录　　
    1. 将流通记录设置为取消　　
    2. 优惠券状态设置为　未使用
    """
    customer = get_customer_by_django_user(user)
    record = get_transfer_record_by_id(transfer_record_id)
    if record.transfer_type != CouponTransferRecord.IN_RETURN_COUPON:
        raise Exception('记录类型有错')
    if record.transfer_status != CouponTransferRecord.PENDING:
        raise Exception('记录状态不在待审核')
    mama = customer.get_charged_mama()
    if record.coupon_to_mama_id != mama.id:
        raise Exception('记录审核人错误')
    record.transfer_status = CouponTransferRecord.CANCELED  # 取消状态
    record.save(update_fields=['transfer_status', 'modified'])
    coupons = get_freeze_boutique_coupons_by_transfer(record.id)
    coupon_ids = [i['id'] for i in coupons.values('id')]
    rollback_user_coupon_status_2_unused_by_ids(coupon_ids)  # 状态设置为未使用
    return True


@transaction.atomic()
def agree_apply_transfer_record_2_sys(transfer_record_id, user=None):
    # type: (DjangoUser, int) -> bool
    """ 同意用户的 退券 到系统
    """
    from .usercoupon import cancel_coupon_by_ids
    from flashsale.xiaolumm.tasks.tasks_mama_dailystats import task_calc_xlmm_elite_score

    record = get_transfer_record_by_id(transfer_record_id)

    coupons = get_freeze_boutique_coupons_by_transfer(record.id)
    if not coupons:
        raise Exception('优惠券没有找到')
    bglog = BudgetLog.objects.get_pending_return_boutique_coupon().filter(referal_id=str(record.id)).first()
    if not bglog:
        raise Exception('用户钱包没有该条记录')
    cancel_coupon_by_ids([i.id for i in coupons])  # 取消优惠券
    bglog.confirm_budget_log()  # 确定钱包金额
    record.transfer_status = CouponTransferRecord.DELIVERED
    record.save(update_fields=['transfer_status', 'modified'])  # 完成流通记录
    if user:
        log_action(user, record, CHANGE, '同意用户申请退券退金额')
    task_calc_xlmm_elite_score(record.coupon_from_mama_id)  # 重算积分
    return True


@transaction.atomic()
def cancel_return_2_sys_transfer(transfer_record_id, customer=None, admin_user=None):
    # type: (int, Customer) -> bool
    """用户取消　退　精品券　给　系统
    """
    record = get_transfer_record_by_id(transfer_record_id)
    if customer:  # 用户提交 校验 用户身份和记录 是否一致
        mama = customer.get_xiaolumm()
        if not record.coupon_from_mama_id != mama.id:
            raise Exception('用户记录错误')
    coupons = get_freeze_boutique_coupons_by_transfer(transfer_record_id)
    if not coupons:
        raise Exception('优惠券没有找到')
    bglog = BudgetLog.objects.get_pending_return_boutique_coupon().filter(referal_id=str(record.id)).first()
    if not bglog:
        raise Exception('用户钱包没有找到记录')
    rollback_user_coupon_status_2_unused_by_ids([cou.id for cou in coupons])  # 优惠券设置为可以使用状态
    bglog.cancel_budget_log()  # 取消钱包记录
    record.transfer_status = CouponTransferRecord.CANCELED  # 取消 申请流通券记录
    record.save(update_fields=['transfer_status', 'modified'])
    if admin_user:
        log_action(admin_user, record, CHANGE, u'拒绝用户申请')
    else:
        log_action(customer.user, record, CHANGE, u'用户取消申请')
    return True


def set_transfer_record_complete(transfer_record):
    # type: (CouponTransferRecord) ->None
    """设置流通记录为已经完成状态
    """
    transfer_record.transfer_status = CouponTransferRecord.DELIVERED
    transfer_record.save(['transfer_status', 'modified'])


def cancel_transfer_record_by_trade(trade_tid):
    # type: (text_type) -> bool
    """因为 订单取消(用户手动 或者 超出支付时间 系统自动 取消)  取消掉流通券记录
    """
    transfer_record = CouponTransferRecord.objects.filter(uni_key=trade_tid).first()
    if not transfer_record:
        return False
    transfer_record.transfer_status = CouponTransferRecord.CANCELED  # 取消
    transfer_record.save(['transfer_status', 'modified'])
