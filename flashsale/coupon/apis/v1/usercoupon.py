# coding=utf-8
from __future__ import unicode_literals, absolute_import

__ALL__ = [
    'release_coupon_for_mama_deposit'
]
from ...tasks.usercoupon import task_release_coupon_for_deposit


def release_coupon_for_deposit(customer_id, deposit_type):
    task_release_coupon_for_deposit.delay(customer_id, deposit_type)

