# coding: utf8
from __future__ import absolute_import, unicode_literals

from datetime import datetime
from django.core.management.base import BaseCommand

from flashsale.pay.models import ModelProduct
from flashsale.coupon.models import CouponTemplate

class Command(BaseCommand):
    def handle(self, *args, **options):
        ### step 1，清理异常精品券
        templates = CouponTemplate.objects.filter(
            coupon_type=CouponTemplate.TYPE_TRANSFER, status=CouponTemplate.SENDING
        )

        error_dict = {}
        template_count = 0
        print 'total_sending_transfer_coupon:', templates.count()
        for template in templates.iterator():
            extras = template.extras
            usual_modelproduct_id = extras.get('scopes', {}).get('modelproduct_ids')
            coupon_modelproduct_id = extras.get('product_model_id')
            if not coupon_modelproduct_id or usual_modelproduct_id == '%s'%coupon_modelproduct_id:
                # print '=================',template.id
                continue
            usual_mp = ModelProduct.objects.filter(id=usual_modelproduct_id).first()
            coupon_mp = ModelProduct.objects.filter(id=coupon_modelproduct_id).first()
            if not usual_mp:
                # print '+++++++++++++++++', template.id, template.title
                continue
            usual_relate_coupon = usual_mp.extras.get('payinfo',{}).get('coupon_template_ids')
            if usual_relate_coupon and usual_relate_coupon[0] != template.id:
                print template.id, usual_relate_coupon, template.title

        print 'end_count:', template_count

        ### step 2, 设置精品券参数 coupon_modelproduct_id