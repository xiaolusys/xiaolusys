# coding=utf-8
from __future__ import absolute_import, unicode_literals
import datetime
from shopmanager import celery_app as app
from django.db import IntegrityError

import logging
logger = logging.getLogger(__name__)


@app.task()
def task_send_transfer_coupons(customer_id, order_id, order_oid, order_num, product_id):
    # type: (int, int, text_type, int, int) -> None
    """创建精品券记录　和　优惠券记录
    """
    from flashsale.pay.apis.v1.customer import get_customer_by_id
    from shopback.items.models import Product
    from flashsale.pay.models import ModelProduct
    from flashsale.coupon.models import CouponTransferRecord
    from ..apis.v1.usercoupon import create_user_coupon
    from ..apis.v1.coupontemplate import get_coupon_template_by_id
    from .coupontemplate import task_update_tpl_released_coupon_nums

    customer = get_customer_by_id(customer_id)
    product = Product.objects.filter(id=product_id).first()
    model_product = ModelProduct.objects.filter(id=product.model_id).first()
    template_id = model_product.extras.get("template_id")

    template = get_coupon_template_by_id(id=template_id)
    index = 0
    while index < order_num:
        unique_key = template.gen_usercoupon_unikey(order_id, index)
        try:
            create_user_coupon(customer.id, template.id, unique_key=unique_key)
        except IntegrityError as e:
            logging.error(e)
        index += 1

    to_mama = customer.get_charged_mama()
    to_mama_nick = customer.nick
    to_mama_thumbnail = customer.thumbnail

    coupon_to_mama_id = to_mama.id
    init_from_mama_id = to_mama.id

    coupon_from_mama_id = 0
    from_mama_thumbnail = 'http://7xogkj.com2.z0.glb.qiniucdn.com/222-ohmydeer.png?imageMogr2/thumbnail/60/format/png'
    from_mama_nick = 'SYSTEM'

    transfer_type = CouponTransferRecord.IN_BUY_COUPON
    date_field = datetime.date.today()
    transfer_status = CouponTransferRecord.DELIVERED
    uni_key = "%s-%s" % (to_mama.id, order_id)
    coupon_value = int(template.value)
    product_img = template.extras.get("product_img") or ''
    elite_score = product.elite_score * (int(order_num))

    try:
        coupon = CouponTransferRecord(coupon_from_mama_id=coupon_from_mama_id, from_mama_thumbnail=from_mama_thumbnail,
                                      from_mama_nick=from_mama_nick, coupon_to_mama_id=coupon_to_mama_id,
                                      to_mama_thumbnail=to_mama_thumbnail, to_mama_nick=to_mama_nick,
                                      coupon_value=coupon_value,
                                      init_from_mama_id=init_from_mama_id, order_no=order_oid, template_id=template_id,
                                      product_img=product_img, coupon_num=order_num, transfer_type=transfer_type, product_id=product_id, elite_score=elite_score,
                                      uni_key=uni_key, date_field=date_field, transfer_status=transfer_status)
        coupon.save()
    except IntegrityError as e:
        logging.error(e)

    task_update_tpl_released_coupon_nums(template.id)  # 统计发放数量
