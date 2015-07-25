# coding=utf-8
from models_coupon import Integral, IntegralLog, Coupon, CouponPool
from flashsale.pay.models import SaleTrade, SaleOrder
import datetime
from celery.task import task
from django.db import transaction
"""
任务执行去检查订单的状态 如果订单的状态确定  即可修改 积分状态为确认状态
"""


@task
@transaction.commit_on_success
def task_Calculate_Users_Integral():
    today = datetime.datetime.today()
    prev_day = today - datetime.timedelta(days=0)
    timefrom = datetime.datetime(prev_day.year, prev_day.month, prev_day.day, 0, 0, 0)
    timeto = datetime.datetime(prev_day.year, prev_day.month, prev_day.day, 23, 59, 59)
    # 遍历昨天(交易完成的)的交易 （其中 SaleTrade status 是 TRADE_FINISHED）
    trades = SaleTrade.objects.filter(modified__gte=timefrom, modified__lte=timeto, status=SaleTrade.TRADE_FINISHED)
    for trade in trades:
        # 找到对应交易的订单  根据订单的id 和buyer_id 操作积分记录
        orders = SaleOrder.objects.filter(sale_trade_id=trade.id)
        # 找到该用户积分汇总记录表
        user_integral, state = Integral.objects.get_or_create(integral_user=trade.buyer_id)
        # 将 PENDING 的积分记录累加到 积分表中
        for order in orders:
            integrallogs = IntegralLog.objects.filter(integral_user=trade.buyer_id, order_id=order.id,
                                                      log_status=IntegralLog.PENDING, in_out=IntegralLog.LOG_IN)
            for ilog in integrallogs:
                # 修改 PENDING 为CONFIRM
                ilog.log_status = IntegralLog.CONFIRM
                # 写入汇总记录中
                user_integral.integral_value += ilog.log_value
                user_integral.save()
                order_content = '[{"order_id":"%s","pic_link":"%s","trade_id":"%s","order_status":"%s"}]' % (
                    str(order.id), str(order.pic_path), str(order.sale_trade_id), str(order.status))
                ilog.order = order_content
                ilog.save()


@task
@transaction.commit_on_success
def task_Update_CouponPoll_Status():
    today = datetime.datetime.today()
    # 定时更新优惠券的状态:超过截至时间的优惠券 将其状态修改为过期无效状态
    # 找到截至时间 是昨天的 优惠券
    deadline_time = datetime.datetime(today.year, today.month, today.day, 0, 0, 0) - datetime.timedelta(days=1)
    # 未发放的 已经发放的 可以使用的  （截至时间是昨天的）
    cous = CouponPool.objects.filter(deadline=deadline_time,
                                     coupon_status__in=(CouponPool.RELEASE, CouponPool.UNRELEASE, CouponPool.PULLED))
    for cou in cous:
        cou.coupon_status = CouponPool.PAST  # 修改为无效的优惠券
        cou.save()
