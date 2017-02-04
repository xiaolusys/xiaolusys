# -*- encoding:utf-8 -*-
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

import sys
import datetime
from django.db import IntegrityError
from django.db.models import F, Sum

from flashsale.xiaolumm import util_unikey
from flashsale.xiaolumm.models.models_fortune import DailyStats, UniqueVisitor, OrderCarry, CarryRecord

import logging
logger = logging.getLogger('celery.handler')



def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    # return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


def create_dailystats_with_integrity(mama_id, date_field, uni_key, **kwargs):
    stats = DailyStats(mama_id=mama_id, date_field=date_field, uni_key=uni_key, **kwargs)
    stats.save()

    # try:
    #    stats = DailyStats(mama_id=mama_id, date_field=date_field, uni_key=uni_key, **kwargs)
    #    stats.save()
    # except IntegrityError as e:
    #    logger.warn("IntegrityError - DailyStats | mama_id: %s, uni_key: %s, params: %s" % (mama_id, uni_key, kwargs))
    # The following will very likely cause deadlock, since another
    # thread is creating this record. we decide to just fail it.
    # DailyStats.objects.filter(mama_id=mama_id, date_field=date_field, uni_key=uni_key).update(**kwargs)


@app.task()
def task_confirm_previous_dailystats(mama_id, today_date_field, num_days):
    # print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    end_date_field = today_date_field - datetime.timedelta(days=num_days)
    records = DailyStats.objects.filter(mama_id=mama_id, date_field__lte=end_date_field, status=1).order_by(
        '-date_field')[:7]
    if records.count() <= 0:
        return

    for stats in records:
        date_field = stats.date_field
        today_visitor_num = UniqueVisitor.objects.filter(mama_id=mama_id, date_field=date_field).count()
        stats.today_visitor_num = today_visitor_num

        today_order_num = OrderCarry.objects.filter(mama_id=mama_id, date_field=date_field).count()
        stats.today_order_num = today_order_num

        carrys = CarryRecord.objects.filter(mama_id=mama_id, date_field=date_field).exclude(status=3).values(
            'date_field').annotate(carry=Sum('carry_num'))
        today_carry_num = 0
        if len(carrys) > 0:
            if carrys[0]["date_field"] == date_field:
                today_carry_num = carrys[0]["carry"]

        stats.today_carry_num = today_carry_num
        stats.status = 2  # confirm
        stats.save()


@app.task(max_retries=3, default_retry_delay=6)
def task_visitor_increment_dailystats(mama_id, date_field):
    # print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    uni_key = util_unikey.gen_dailystats_unikey(mama_id, date_field)
    #if len(uni_key) > 16:
    #    logger.error("%s: create dailystats error: uni_key wrong %s" % (get_cur_info(), uni_key))

    records = DailyStats.objects.filter(uni_key=uni_key)

    if records.count() <= 0:
        try:
            create_dailystats_with_integrity(mama_id, date_field, uni_key, today_visitor_num=1)
        except IntegrityError as exc:
            #logger.error(
            #    "IntegrityError - DailyStats | %s, mama_id: %s, uni_key: %s, today_visitor_num=1" % (get_cur_info(), mama_id, uni_key))
            raise task_visitor_increment_dailystats.retry(exc=exc)
    else:
        records.update(today_visitor_num=F('today_visitor_num') + 1)


@app.task(max_retries=3, default_retry_delay=6)
def task_carryrecord_update_dailystats(mama_id, date_field):
    uni_key = util_unikey.gen_dailystats_unikey(mama_id, date_field)

    records = DailyStats.objects.filter(uni_key=uni_key)
    carrys = CarryRecord.objects.filter(mama_id=mama_id, date_field=date_field).exclude(status=3).values(
        'date_field').annotate(carry=Sum('carry_num'))

    today_carry_num = 0
    if len(carrys) > 0:
        if carrys[0]["date_field"] == date_field:
            today_carry_num = carrys[0]["carry"]

    if records.count() <= 0:
        try:
            create_dailystats_with_integrity(mama_id, date_field, uni_key, today_carry_num=today_carry_num)
        except IntegrityError as exc:
            raise task_carryrecord_update_dailystats.retry(exc=exc)
    else:
        records.update(today_carry_num=today_carry_num)


@app.task(max_retries=3, default_retry_delay=6)
def task_ordercarry_increment_dailystats(mama_id, date_field):
    # print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    uni_key = util_unikey.gen_dailystats_unikey(mama_id, date_field)
    #if len(uni_key) > 16:
    #    logger.error("%s: create dailystats error: uni_key wrong %s" % (get_cur_info(), uni_key))

    records = DailyStats.objects.filter(uni_key=uni_key)

    if records.count() <= 0:
        try:
            create_dailystats_with_integrity(mama_id, date_field, uni_key, today_order_num=1)
        except IntegrityError as exc:
            #logger.error(
            #    "IntegrityError - DailyStats | %s, mama_id: %s, uni_key: %s, today_order_num=1" % (get_cur_info(), mama_id, uni_key))
            raise task_ordercarry_increment_dailystats.retry(exc=exc)
    else:
        records.update(today_order_num=F('today_order_num') + 1)


@app.task()
def task_xlmm_score():
    from flashsale.xiaolumm.models.score import XlmmEffectScore, XlmmTeamEffScore
    XlmmEffectScore.batch_generate()
    XlmmTeamEffScore.batch_generate()


@app.task()
def task_check_xlmm_exchg_order():
    tt = datetime.datetime.now()
    tf = tt - datetime.timedelta(days=30)

    queryset = OrderCarry.objects.filter(carry_type__in=[OrderCarry.WAP_ORDER, OrderCarry.APP_ORDER],
                                         status__in=[OrderCarry.CONFIRM, OrderCarry.CANCEL],
                                         created__gte=tf)
    exchg_orders = [i['order_id'] for i in queryset.values('order_id')]
    from flashsale.pay.models.trade import SaleOrder
    new_elite_queryset = SaleOrder.objects.filter(item_id='80281', status=SaleOrder.TRADE_FINISHED)
    new_elite_orders = [i['oid'] for i in new_elite_queryset.values('oid')]
    exchg_orders = set(exchg_orders) | set(new_elite_orders)

    order_num = 0
    succ_coupon_record_num = 0
    succ_exchg_coupon_num = 0
    succ_exchg_goods_payment = 0
    exchg_goods_num = 0
    exchg_goods_payment = 0
    exchg_budget_sum = 0
    exchg_trancoupon_num = 0
    results = []
    if exchg_orders:
        for order_id in exchg_orders:
            # find sale trade use coupons
            sale_order = SaleOrder.objects.filter(oid=order_id).first()
            if not sale_order:
                continue
            if sale_order and sale_order.extras.has_key('exchange') \
                    and (sale_order.status not in [SaleOrder.TRADE_CLOSED_BY_SYS]):
                order_num += 1
                if sale_order.item_id == '80281':
                    exchg_goods_num += round(sale_order.payment / 68)
                else:
                    exchg_goods_num += round(sale_order.payment / sale_order.price)
                exchg_goods_payment += round(sale_order.payment * 100)
                results.append(order_id)
                if sale_order.extras['exchange'] == True:
                    succ_exchg_goods_payment += round(sale_order.payment * 100)
                    from flashsale.coupon.models.usercoupon import UserCoupon
                    user_coupons = UserCoupon.objects.filter(trade_tid=order_id,
                                                             status=UserCoupon.USED)
                    if user_coupons:
                        succ_coupon_record_num += 1
                        succ_exchg_coupon_num += user_coupons.count()
                    else:
                        # 可能有物流丢单破损等重新发货的场景，那么需要更新usercoupon oid
                        if '-' in order_id:
                            oid = order_id.split('-')
                            user_coupons = UserCoupon.objects.filter(trade_tid=oid[0],
                                                                     status=UserCoupon.USED)
                            if user_coupons:
                                succ_coupon_record_num += 1
                                succ_exchg_coupon_num += user_coupons.count()
                                for special_coupon in user_coupons:
                                    special_coupon.trade_tid = order_id
                                    special_coupon.save()
                            else:
                                print 'error1', sale_order.oid
                        else:
                            print 'error2', sale_order.oid

    from flashsale.pay.models.user import BudgetLog
    budget_log1 = BudgetLog.objects.filter(budget_type=BudgetLog.BUDGET_IN,
                                          budget_log_type=BudgetLog.BG_EXCHG_ORDER, status=BudgetLog.CONFIRMED, created__gte=tf)
    budget_log2 = BudgetLog.objects.filter(budget_type=BudgetLog.BUDGET_OUT,
                                           budget_log_type=BudgetLog.BG_EXCHG_ORDER, status=BudgetLog.CONFIRMED, created__gte=tf)
    budget_num = budget_log1.count() - budget_log2.count()
    budget_oids = [i['uni_key'] for i in budget_log1.values('uni_key')]
    res1 = BudgetLog.objects.filter(budget_type=BudgetLog.BUDGET_IN,
                                   budget_log_type=BudgetLog.BG_EXCHG_ORDER, status=BudgetLog.CONFIRMED, created__gte=tf).aggregate(
        n=Sum('flow_amount'))
    exchg_budget_sum1 = res1['n'] or 0
    res2 = BudgetLog.objects.filter(budget_type=BudgetLog.BUDGET_OUT,
                                   budget_log_type=BudgetLog.BG_EXCHG_ORDER, status=BudgetLog.CONFIRMED, created__gte=tf).aggregate(
        n=Sum('flow_amount'))
    exchg_budget_sum2 = res2['n'] or 0
    exchg_budget_sum = exchg_budget_sum1 - exchg_budget_sum2
    from flashsale.coupon.models.transfer_coupon import CouponTransferRecord
    trans_num = CouponTransferRecord.objects.filter(transfer_type=CouponTransferRecord.OUT_EXCHG_SALEORDER, transfer_status=CouponTransferRecord.DELIVERED, created__gte=tf).count()
    res = CouponTransferRecord.objects.filter(transfer_type=CouponTransferRecord.OUT_EXCHG_SALEORDER, transfer_status=CouponTransferRecord.DELIVERED, created__gte=tf).aggregate(
        n=Sum('coupon_num'))
    exchg_trancoupon_num = res['n'] or 0
    retD = list(set(results).difference(set(budget_oids)))
    print "results more is: ", retD
    retD = list(set(budget_oids).difference(set(results)))
    print "budget_oids more is: ", retD

    logger.info({'message': u'check exchg order | order_num=%s == budget_num=%s == trans_num=%s ?' % (order_num,budget_log1.count(),trans_num),
                 'message2': u' exchg_goods_num=%s == exchg_trancoupon_num=%s' % (exchg_goods_num, exchg_trancoupon_num),
                 'message3': u'succ_coupon_record_num=%s == succ budget_num=%s' % (succ_coupon_record_num, budget_num),
                 'message4': u'exchged_goods_payment(include return exchg)=%s == exchg_budget_sum=%s , succ_exchg_goods_payment=%s == exchg_budget_sum=%s' % (exchg_goods_payment, exchg_budget_sum1, succ_exchg_goods_payment, exchg_budget_sum)
                })
    if order_num != budget_log1.count() or order_num != trans_num:
        from common.dingding import DingDingAPI
        tousers = [
            '02401336675559',  # 伍磊
        ]
        msg = '定时检查boutique exchange数据:\n时间: %s \norder_num=%s == budget_num=%s == trans_num=%s\n' % \
              (str(datetime.datetime.now()), order_num, budget_log1.count(), trans_num)
        dd = DingDingAPI()
        for touser in tousers:
            dd.sendMsg(msg, touser)


@app.task()
def task_check_xlmm_return_exchg_order():
    from flashsale.pay.models.user import BudgetLog
    exchg_orders = BudgetLog.objects.filter(budget_log_type=BudgetLog.BG_EXCHG_ORDER, status=BudgetLog.CONFIRMED)
    order_num = 0
    exchg_goods_num = 0
    exchg_goods_payment = 0
    exchg_budget_sum = 0
    exchg_trancoupon_num = 0
    return_order_num = 0
    results = []
    if exchg_orders:
        for entry in exchg_orders:
            # find sale trade use coupons
            from flashsale.pay.models.trade import SaleOrder
            from flashsale.pay.models.refund import SaleRefund
            sale_order = SaleOrder.objects.filter(oid=entry.uni_key).first()
            if not sale_order:
                continue
            if sale_order and sale_order.extras.has_key('exchange') and sale_order.extras['exchange'] == False:
                order_num += 1
                exchg_goods_num += sale_order.payment / sale_order.price
                exchg_goods_payment += round(sale_order.payment * 100)
                results.append(sale_order.sale_trade.tid)
            if sale_order and (sale_order.status == SaleOrder.TRADE_CLOSED or sale_order.refund_status != SaleRefund.NO_REFUND):
                return_order_num += 1
    budget_log = BudgetLog.objects.filter(budget_type=BudgetLog.BUDGET_OUT, budget_log_type=BudgetLog.BG_EXCHG_ORDER, status=BudgetLog.CONFIRMED)
    budget_num = budget_log.count()
    budget_oids = [i['uni_key'] for i in budget_log.values('uni_key')]
    res = BudgetLog.objects.filter(budget_type=BudgetLog.BUDGET_OUT, budget_log_type=BudgetLog.BG_EXCHG_ORDER, status=BudgetLog.CONFIRMED).aggregate(n=Sum('flow_amount'))
    exchg_budget_sum = res['n'] or 0
    from flashsale.coupon.models.transfer_coupon import CouponTransferRecord
    trans_records = CouponTransferRecord.objects.filter(transfer_type=CouponTransferRecord.IN_RETURN_GOODS, transfer_status=CouponTransferRecord.DELIVERED)
    trans_num = 0
    for record in trans_records:
        if record.order_no in results:
            trans_num += 1
            exchg_trancoupon_num += record.coupon_num
    retD = list(set(results).difference(set(budget_oids)))
    retD = list(set(budget_oids).difference(set(results)))

    logger.info({'message': u'check return exchg order | order_num=%s == budget_num=%s == trans_num=%s maybe!= return_order_num(include not finish refund) %s?' % (order_num,budget_num,trans_num,return_order_num),
                 'message2': u' exchg_goods_num=%s == exchg_trancoupon_num=%s' % (exchg_goods_num, exchg_trancoupon_num),
                 'message3': u'exchg_goods_payment=%s == exchg_budget_sum=%s' % (exchg_goods_payment, exchg_budget_sum)
                })
    if order_num != budget_num or order_num != trans_num:
        from common.dingding import DingDingAPI
        tousers = [
            '02401336675559',  # 伍磊
        ]
        msg = '定时检查boutique return exchange数据:\n时间: %s \norder_num=%s == budget_num=%s == trans_num=%s\n' % \
              (str(datetime.datetime.now()), order_num, budget_num, trans_num)
        dd = DingDingAPI()
        for touser in tousers:
            dd.sendMsg(msg, touser)


@app.task(max_retries=3, default_retry_delay=6)
def task_calc_xlmm_elite_score(mama_id):
    if mama_id <= 0:
        return
    from flashsale.coupon.models.transfer_coupon import CouponTransferRecord
    from flashsale.xiaolumm.models.models import XiaoluMama

    res = CouponTransferRecord.objects.filter(
        coupon_from_mama_id=mama_id,
        transfer_status=CouponTransferRecord.DELIVERED,
        transfer_type__in=[CouponTransferRecord.OUT_CASHOUT, CouponTransferRecord.IN_RETURN_COUPON]
    ).aggregate(n=Sum('elite_score'))
    out_score = res['n'] or 0

    res = CouponTransferRecord.objects.filter(
        coupon_to_mama_id=mama_id,
        transfer_status=CouponTransferRecord.DELIVERED,
        transfer_type__in=[CouponTransferRecord.IN_BUY_COUPON, CouponTransferRecord.OUT_TRANSFER, CouponTransferRecord.IN_GIFT_COUPON, CouponTransferRecord.IN_RECHARGE]
    ).aggregate(n=Sum('elite_score'))
    in_score = res['n'] or 0

    score = in_score - out_score
    XiaoluMama.objects.filter(id=mama_id).update(elite_score=score)


@app.task()
def task_calc_all_xlmm_elite_score():
    from flashsale.coupon.models.transfer_coupon import CouponTransferRecord
    import datetime
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    records = CouponTransferRecord.objects.filter(status=CouponTransferRecord.EFFECT, date_field__gte=yesterday)
    to_mms = [c['coupon_to_mama_id'] for c in records.values('coupon_to_mama_id')]
    from_mms = [c['coupon_from_mama_id'] for c in records.values('coupon_from_mama_id')]
    elite_mamas = set(to_mms) | set(from_mms)

    mama_count = 0
    for mama in elite_mamas:
        if mama > 0:
            task_calc_xlmm_elite_score.delay(mama)
            mama_count += 1
    logger.info({'message': u'cacl elite score | mama count=%s' % (mama_count), })

    task_check_xlmm_exchg_order.delay()
    task_check_xlmm_return_exchg_order.delay()


def check_xlmm_ordercarry(recent_day):
    results = []

    tt = datetime.datetime.now()
    tf = tt - datetime.timedelta(days=recent_day)
    from flashsale.pay.models.trade import SaleOrder, SaleTrade, Customer
    queryset = SaleOrder.objects.filter(status__in=[SaleOrder.WAIT_SELLER_SEND_GOODS,
                                                    SaleOrder.WAIT_BUYER_CONFIRM_GOODS,
                                                    SaleOrder.TRADE_BUYER_SIGNED,
                                                    SaleOrder.TRADE_FINISHED,
                                                    SaleOrder.TRADE_CLOSED,
                                                    SaleOrder.TRADE_CLOSED_BY_SYS],
                                        created__gte=tf)

    for order in queryset:
        # 特卖订单有ordercarry或用币买券的inderect mama 虚拟订单有
        coin_buy_order = False
        from flashsale.xiaolumm.models import XiaoluMama
        from flashsale.pay.apis.v1.order import get_pay_type_from_trade
        if order.sale_trade.order_type == SaleTrade.ELECTRONIC_GOODS_ORDER:
            budget_pay, coin_pay = get_pay_type_from_trade(order.sale_trade)
            if coin_pay:
                customer = Customer.objects.get(id=order.buyer_id)
                to_mama = customer.get_xiaolumm()
                if to_mama.referal_from == XiaoluMama.INDIRECT:
                    coin_buy_order = True
        if order.sale_trade.order_type == SaleTrade.SALE_ORDER or coin_buy_order:
            order_carry_qs = OrderCarry.objects.filter(order_id=order.oid)
            if not order_carry_qs:
                from flashsale.xiaolumm.tasks import task_order_trigger
                task_order_trigger(order)
                order_carry_qs = OrderCarry.objects.filter(order_id=order.oid)
                if order_carry_qs:
                    results.append(order.oid)
                continue
            status = OrderCarry.STAGING  # unpaid
            if order.need_send():
                status = OrderCarry.ESTIMATE
            elif order.is_confirmed():
                status = OrderCarry.CONFIRM
            elif order.is_canceled():
                status = OrderCarry.CANCEL

            update_fields = ['status', 'modified']
            for order_carry in order_carry_qs:
                if status != order_carry.status:
                    from core.options import log_action, CHANGE, get_systemoa_user
                    logmsg = 'status not equal to saleorder|status:%s->%s' % (
                        order_carry.status, status)
                    order_carry.status = status
                    order_carry.save(update_fields=update_fields)
                    sys_oa = get_systemoa_user()
                    log_action(sys_oa, order_carry, CHANGE, logmsg)
                    results.append(order.oid)
    print "ordercarry error is: ", results
