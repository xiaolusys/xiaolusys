# coding=utf-8
from __future__ import unicode_literals, absolute_import
from ...models import CouponTemplate

__ALL__ = [
    'get_coupon_template_by_id',
]


def get_coupon_template_by_id(id):
    # type: (int) -> CouponTemplate
    return CouponTemplate.objects.get(id=id)


def get_boutique_coupon_modelid_by_templateid(id):
    from flashsale.coupon.models import CouponTemplate
    ct = CouponTemplate.objects.filter(id=id).first()
    if ct:
        product_model_id = ct.extras.get("product_model_id")
        return product_model_id
    return None

