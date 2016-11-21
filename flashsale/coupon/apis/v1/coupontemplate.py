# coding=utf-8
from __future__ import unicode_literals, absolute_import
from ...models import CouponTemplate

__ALL__ = [
    'get_coupon_template_by_id',
]


def get_coupon_template_by_id(id):
    # type: (int) -> CouponTemplate
    return CouponTemplate.objects.get(id=id)
