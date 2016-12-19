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
    # print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    uni_key = util_unikey.gen_dailystats_unikey(mama_id, date_field)
    #if len(uni_key) > 16:
    #    logger.error("%s: create dailystats error: uni_key wrong %s" % (get_cur_info(), uni_key))

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
            #logger.error("IntegrityError - DailyStats | %s, mama_id: %s, uni_key: %s, today_carry_num=%s" % (get_cur_info(), mama_id, uni_key, today_carry_num))
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
    exchg_orders = OrderCarry.objects.filter(carry_type__in=[OrderCarry.WAP_ORDER, OrderCarry.APP_ORDER],
                                         status__in=[OrderCarry.CONFIRM, OrderCarry.CANCEL],
                                         date_field__gt='2016-11-30')
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
        for entry in exchg_orders:
            # find sale trade use coupons
            from flashsale.pay.models.trade import SaleOrder, SaleTrade
            sale_order = SaleOrder.objects.filter(oid=entry.order_id).first()
            if not sale_order:
                continue
            if sale_order and sale_order.extras.has_key('exchange'):
                order_num += 1
                exchg_goods_num += round(sale_order.payment / sale_order.price)
                exchg_goods_payment += round(sale_order.payment * 100)
                results.append(entry.order_id)
                if sale_order.extras['exchange'] == True:
                    succ_exchg_goods_payment += round(sale_order.payment * 100)
                    from flashsale.coupon.models.usercoupon import UserCoupon
                    user_coupons = UserCoupon.objects.filter(trade_tid=entry.order_id,
                                                             status=UserCoupon.USED)
                    if user_coupons:
                        succ_coupon_record_num += 1
                        succ_exchg_coupon_num += user_coupons.count()
                    else:
                        print 'error', sale_order.oid
                else:
                    print sale_order.oid
    from flashsale.pay.models.user import BudgetLog
    budget_log1 = BudgetLog.objects.filter(budget_type=BudgetLog.BUDGET_IN,
                                          budget_log_type=BudgetLog.BG_EXCHG_ORDER, status=BudgetLog.CONFIRMED)
    budget_log2 = BudgetLog.objects.filter(budget_type=BudgetLog.BUDGET_OUT,
                                           budget_log_type=BudgetLog.BG_EXCHG_ORDER, status=BudgetLog.CONFIRMED)
    budget_num = budget_log1.count() - budget_log2.count()
    budget_oids = [i['uni_key'] for i in budget_log1.values('uni_key')]
    res1 = BudgetLog.objects.filter(budget_type=BudgetLog.BUDGET_IN,
                                   budget_log_type=BudgetLog.BG_EXCHG_ORDER, status=BudgetLog.CONFIRMED).aggregate(
        n=Sum('flow_amount'))
    exchg_budget_sum1 = res1['n'] or 0
    res2 = BudgetLog.objects.filter(budget_type=BudgetLog.BUDGET_OUT,
                                   budget_log_type=BudgetLog.BG_EXCHG_ORDER, status=BudgetLog.CONFIRMED).aggregate(
        n=Sum('flow_amount'))
    exchg_budget_sum2 = res2['n'] or 0
    exchg_budget_sum = exchg_budget_sum1 - exchg_budget_sum2
    from flashsale.coupon.models.transfer_coupon import CouponTransferRecord
    trans_num = CouponTransferRecord.objects.filter(transfer_type=CouponTransferRecord.OUT_EXCHG_SALEORDER, transfer_status=CouponTransferRecord.DELIVERED).count()
    res = CouponTransferRecord.objects.filter(transfer_type=CouponTransferRecord.OUT_EXCHG_SALEORDER, transfer_status=CouponTransferRecord.DELIVERED).aggregate(
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
    print "results more is: ", retD
    retD = list(set(budget_oids).difference(set(results)))
    print "budget_oids more is: ", retD

    logger.info({'message': u'check return exchg order | order_num=%s == budget_num=%s == trans_num=%s maybe!= return_order_num(include not finish refund) %s?' % (order_num,budget_num,trans_num,return_order_num),
                 'message2': u' exchg_goods_num=%s == exchg_trancoupon_num=%s' % (exchg_goods_num, exchg_trancoupon_num),
                 'message3': u'exchg_goods_payment=%s == exchg_budget_sum=%s' % (exchg_goods_payment, exchg_budget_sum)
                })


@app.task()
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
        transfer_type=CouponTransferRecord.IN_BUY_COUPON
    ).aggregate(n=Sum('elite_score'))
    in_buy_score = res['n'] or 0

    res = CouponTransferRecord.objects.filter(
        coupon_to_mama_id=mama_id,
        transfer_status=CouponTransferRecord.DELIVERED,
        transfer_type=CouponTransferRecord.OUT_TRANSFER
    ).aggregate(n=Sum('elite_score'))
    in_trans_score = res['n'] or 0

    score = in_buy_score + in_trans_score - out_score
    XiaoluMama.objects.filter(id=mama_id).update(elite_score=score)


@app.task()
def task_calc_all_xlmm_elite_score():
    from flashsale.xiaolumm.models.models import XiaoluMama
    elite_mamas = XiaoluMama.objects.filter(status=XiaoluMama.EFFECT, charge_status=XiaoluMama.CHARGED,
                                            referal_from__in=[XiaoluMama.DIRECT, XiaoluMama.INDIRECT])

    mama_count = 0
    for mama in elite_mamas:
        is_elite = (mama.referal_from == XiaoluMama.DIRECT) or (mama.referal_from == XiaoluMama.INDIRECT)
        if is_elite:
            task_calc_xlmm_elite_score.delay(mama.id)
            mama_count += 1
    logger.info({'message': u'cacl elite score | mama count=%s' % (mama_count), })

    task_check_xlmm_exchg_order.delay()
    task_check_xlmm_return_exchg_order.delay()


