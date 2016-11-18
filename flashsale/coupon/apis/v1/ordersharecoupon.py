# coding=utf-8
from __future__ import absolute_import, unicode_literals
from ...models import OrderShareCoupon
from .coupontemplate import get_coupon_template_by_id

__ALL__ = [
    'get_order_share_coupon_by_id',
    'create_share_coupon',
]


def get_order_share_coupon_by_id(id):
    # type: (int) -> OrderShareCoupon
    return OrderShareCoupon.objects.get(id=id)


def create_share_coupon(coupon_template_id, customer_id, uniq_id, ufrom, customer_nick='', customer_thumbnail=''):
    # type: (int, int, text_type, text_type, text_type, text_type) -> OrderShareCoupon
    """ create order share coupon record
    """
    template = get_coupon_template_by_id(coupon_template_id)
    ocs = OrderShareCoupon.filter(share_customer=customer_id, template_id=template.id, uniq_id=uniq_id).first()
    if ocs:
        return ocs
    extras = {
        'user_info':
            {'id': customer_id, 'nick': customer_nick, 'thumbnail': customer_thumbnail},
        'templates':
            {'post_img': template.post_img,
             'title': template.title,
             'description': template.description}  # 优惠券模板
    }
    value, start_use_time, expires_time = template.calculate_value_and_time()
    osc = OrderShareCoupon(
        template_id=template.id,
        share_customer=customer_id,
        uniq_id=uniq_id,
        limit_share_count=template.share_times_limit,
        platform_info={ufrom: 1},
        share_start_time=start_use_time,
        share_end_time=expires_time,
        extras=extras,
    )
    return osc
