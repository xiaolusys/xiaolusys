# coding=utf-8
from models_coupon import CouponPool
import datetime
from celery.task import task
from django.db import transaction
"""
任务执行去检查订单的状态 如果订单的状态确定  即可修改 积分状态为确认状态
"""

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
