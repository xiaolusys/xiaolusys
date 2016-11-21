# coding=utf-8
from __future__ import absolute_import, unicode_literals

from shopmanager import celery_app as app
import logging

logger = logging.getLogger(__name__)


@app.task(serializer='pickle')
def task_update_tpl_released_coupon_nums(coupon_template_id):
    # type:(int) -> None
    """当发放用户优惠券时候更新模板的发放数量
    """
    from flashsale.coupon.models import UserCoupon
    from ..apis.v1.coupontemplate import get_coupon_template_by_id

    template = get_coupon_template_by_id(coupon_template_id)
    count = UserCoupon.objects.get_template_coupons(coupon_template_id).count()
    template.has_released_count = count
    template.save(update_fields=['has_released_count'])
