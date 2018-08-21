# coding=utf-8
from __future__ import absolute_import, unicode_literals

from shopmanager import celery_app as app
import logging

logger = logging.getLogger(__name__)


@app.task()
def task_update_share_coupon_release_count(share_coupon_id):
    # type: (int) -> None
    """当有分享类型优惠券发放的时候更新分享记录的优惠券数量
    """
    from flashsale.coupon.models import UserCoupon
    from ..apis.v1.ordersharecoupon import get_order_share_coupon_by_id

    share_coupon = get_order_share_coupon_by_id(share_coupon_id)
    count = UserCoupon.objects.get_order_share_coupons(share_coupon_id).count()
    share_coupon.release_count = count
    share_coupon.save(update_fields=['release_count'])
