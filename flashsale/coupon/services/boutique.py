# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
from django.db import transaction, IntegrityError
from flashsale.coupon.models import CouponTemplate

@transaction.atomic
def get_or_create_boutique_template(model_id, model_price, model_product_ids=[], model_title='', model_img=''):

    boutique_no = '%s-boutique-%s'%(CouponTemplate.PREFIX_NO, model_id)
    ct = CouponTemplate.objects.select_for_update().filter(template_no=boutique_no).first()
    try:
        if not ct:
            time_now = datetime.datetime.now()
            ct = CouponTemplate(template_no=boutique_no)
            ct.title = '精品|' + model_title.split('|')[-1].split('｜')[-1]
            ct.prepare_release_num = 10000
            ct.value = model_price
            ct.coupon_type = CouponTemplate.TYPE_TRANSFER
            ct.status = CouponTemplate.SENDING
            ct.release_start_time = time_now
            ct.release_end_time = time_now + datetime.timedelta(days=2 * 365)
            ct.use_deadline = time_now + datetime.timedelta(days=3 * 365)
            ct.scope_type = CouponTemplate.SCOPE_PRODUCT
            ct.extras["release"].update({"use_min_payment": 0, "limit_after_release_days": 365})

        ct.extras["scopes"].update({"product_ids": model_product_ids})
        ct.extras.update({"product_model_id": int(model_id), "product_img": model_img})
        ct.save()
    except IntegrityError:
        ct = CouponTemplate.objects.get(template_no=boutique_no)

    return ct