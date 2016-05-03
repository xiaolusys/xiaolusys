# coding=utf-8

from celery.task import task
from django.db.models import F


@task()
def task_update_tpl_released_coupon_nums(template):
    """
    template : CouponTemplate instance
    has_released_count ++ when the CouponTemplate release success.
    """
    template.has_released_count = F('has_released_count') + 1
    template.save(update_fields=['has_released_count'])


@task()
def task_update_share_coupon_release_count(share_coupon):
    """
    share_coupon : OrderShareCoupon instance
    release_count ++ when the OrderShareCoupon release success
    """
    share_coupon.release_count = F('release_count') + 1
    share_coupon.save(update_fields=['release_count'])
