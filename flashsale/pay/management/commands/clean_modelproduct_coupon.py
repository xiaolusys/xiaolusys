# coding: utf8
from __future__ import absolute_import, unicode_literals

from datetime import datetime
from django.core.management.base import BaseCommand

from flashsale.pay.models import ModelProduct
from flashsale.coupon.models import CouponTemplate

class Command(BaseCommand):

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('action', nargs='+', type=str)

    def handle(self, *args, **options):
        ### step 1，清理异常精品券
        templates = CouponTemplate.objects.filter(
            coupon_type=CouponTemplate.TYPE_TRANSFER, status=CouponTemplate.SENDING
        )

        moudelproduct_map = {}
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

            if moudelproduct_map.has_key(usual_modelproduct_id):
                moudelproduct_map[usual_modelproduct_id].append(template.id)
            else:
                moudelproduct_map[usual_modelproduct_id] = []
                moudelproduct_map[usual_modelproduct_id].append(template.id)

        for k in moudelproduct_map.keys():
            if len(moudelproduct_map[k]) > 1:
                print 'usual moudelproduct_map', k, moudelproduct_map[k]
        print 'end_count:', template_count

        ### step 2, 设置精品券参数 coupon_modelproduct_id
        action_name = options.get('action')[0]

        if action_name == 'find_error':
            ### step 1，清理异常精品券
            templates = CouponTemplate.objects.filter(
                coupon_type=CouponTemplate.TYPE_TRANSFER, status=CouponTemplate.SENDING
            )

            moudelproduct_map = {}
            error_dict = {}
            template_count = 0
            print 'total_sending_transfer_coupon:', templates.count()
            for template in templates.iterator():
                extras = template.extras
                usual_modelproduct_id = extras.get('scopes', {}).get('modelproduct_ids')
                coupon_modelproduct_id = extras.get('product_model_id')
                if not coupon_modelproduct_id or usual_modelproduct_id == '%s' % coupon_modelproduct_id:
                    # print '=================',template.id
                    continue
                usual_mp = ModelProduct.objects.filter(id=usual_modelproduct_id).first()
                coupon_mp = ModelProduct.objects.filter(id=coupon_modelproduct_id).first()
                if not usual_mp:
                    # print '+++++++++++++++++', template.id, template.title
                    continue
                usual_relate_coupon = usual_mp.extras.get('payinfo', {}).get('coupon_template_ids')
                if usual_relate_coupon and usual_relate_coupon[0] != template.id:
                    print template.id, usual_relate_coupon, template.title

                if moudelproduct_map[usual_modelproduct_id]:
                    moudelproduct_map[usual_modelproduct_id].append(template.id)
                else:
                    moudelproduct_map[usual_modelproduct_id] = []
                    moudelproduct_map[usual_modelproduct_id].append(template.id)

            for mp in moudelproduct_map:
                print mp
            print 'end_count:', template_count

        if action_name == 'add_extras':
            ### step 2, 设置精品券参数 coupon_modelproduct_id
            mp_id_set = set()
            mp_cp_id_map = {}
            error_cp_ids = set()
            goods_cp_ids  = set()
            virtual_values_list = ModelProduct.objects.get_virtual_modelproducts().values_list('id', 'extras')
            for cp_model_id, cp_extras in virtual_values_list:
                cp_template_id = cp_extras.get('template_id')
                if not cp_template_id:
                    print '==========', cp_model_id, cp_template_id
                    continue

                cp_tpl = CouponTemplate.objects.get(id=cp_template_id)
                usual_mp_id = cp_tpl.extras.get('scopes', {}).get('modelproduct_ids')
                if not usual_mp_id:
                    print '++++++++++', cp_template_id, usual_mp_id
                    continue

                usual_mp = ModelProduct.objects.filter(id=usual_mp_id).first()
                if not usual_mp:
                    print '**********', usual_mp_id
                    continue

                if usual_mp_id in mp_id_set:
                    print 'error-------',cp_model_id, usual_mp_id
                    error_cp_ids.add(cp_model_id)
                    cp_model_id = mp_cp_id_map.get(usual_mp_id)
                    error_cp_ids.add(cp_model_id)
                    if cp_model_id in goods_cp_ids:
                        goods_cp_ids.remove(cp_model_id)
                    continue

                mp_id_set.add(usual_mp_id)
                mp_cp_id_map[usual_mp_id] = cp_model_id
                coupon_template_ids = usual_mp.extras.get('payinfo',{}).get('coupon_template_ids')
                if cp_template_id not in coupon_template_ids:
                    error_cp_ids.add(cp_model_id)
                    print 'xxxxxxxxxxx', cp_template_id, usual_mp.id, usual_mp.name
                    continue
                if cp_model_id in goods_cp_ids:
                    print 'eeeeeeeeeee', cp_model_id, cp_tpl.title
                goods_cp_ids.add(cp_model_id)
                # print 'ok:', cp_template_id, usual_mp.id, usual_mp.name
            print 'xxxxxxxxxxxxxxxx ERROR xxxxxxxxxxxxxxxxx', ','.join(map(str, error_cp_ids))
            print '================ COUNT =================', len(goods_cp_ids), ','.join(map(str, goods_cp_ids))
            goods_values_list = ModelProduct.objects.filter(id__in=goods_cp_ids).values_list('id', 'extras')
            for cp_model_id, cp_extras in goods_values_list:
                cp_template_id = cp_extras.get('template_id')
                cp_tpl = CouponTemplate.objects.get(id=cp_template_id)
                usual_mp_id = cp_tpl.extras.get('scopes', {}).get('modelproduct_ids')
                usual_mp = ModelProduct.objects.filter(id=usual_mp_id).first()
                coupon_template_ids = usual_mp.extras.get('payinfo', {}).get('coupon_template_ids')

                if cp_template_id not in coupon_template_ids:
                    print '====error====',cp_template_id, usual_mp.id, usual_mp.name
                if usual_mp.extras['payinfo'].get('coupon_modelproduct_id'):
                    continue

                usual_mp.extras['payinfo']['coupon_modelproduct_id'] = cp_model_id
                usual_mp.save(update_fields=['extras'])
