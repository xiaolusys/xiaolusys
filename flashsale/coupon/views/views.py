# coding=utf-8
from __future__ import absolute_import, unicode_literals
import datetime
from django.db import transaction
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response
from core.options import log_action, CHANGE, ADDITION
from flashsale.pay.models import SaleOrder, Customer, ModelProduct
from collections import OrderedDict

from ..apis.v1.usercoupon import create_user_coupon
from ..apis.v1.transfer import agree_apply_transfer_record_2_sys, cancel_return_2_sys_transfer
from ..models import UserCoupon, CouponTemplate, CouponTransferRecord

import logging

logger = logging.getLogger(__name__)


class ReleaseOmissive(APIView):
    """
    补发遗漏的优惠券
    参数：优惠券模板
    用户：客户信息(用户手机号，或者用户id)
    """
    usercoupons = UserCoupon.objects.all()
    renderer_classes = (JSONRenderer, )
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)

    def get(self, request):
        from shopback.items.models import Product

        content = request.GET
        now = datetime.datetime.now()
        monthago = now - datetime.timedelta(days=30)
        buyer_id = content.get("buyer_id") or 1
        time_from = content.get('time_from') or monthago
        time_to = content.get('time_to') or now

        default_modelids = ModelProduct.objects.filter(product_type=ModelProduct.VIRTUAL_TYPE,
                                                       status=ModelProduct.NORMAL).values('id')
        default_modelids = ','.join([str(m['id']) for m in default_modelids])
        model_ids = content.get("model_ids") or default_modelids
        model_ids_list = [int(i.strip()) for i in model_ids.split(',') if i]
        item_ids = [i['id'] for i in Product.objects.filter(model_id__in=model_ids_list).values('id')]
        # 购券订单
        sale_orders = SaleOrder.objects.filter(pay_time__gte=time_from,
                                               pay_time__lte=time_to,
                                               buyer_id=buyer_id,
                                               item_id__in=item_ids,
                                               status=SaleOrder.TRADE_FINISHED).values('id',
                                                                                       'sale_trade_id',
                                                                                       'status',
                                                                                       'num',
                                                                                       'title')
        # 获取赠送的优惠券
        usercoupons = UserCoupon.objects.filter(customer_id=buyer_id,
                                                created__gte=time_from,
                                                created__lte=time_to,
                                                coupon_type=CouponTemplate.TYPE_TRANSFER,
                                                uniq_id__contains='gift_transfer').values('id',
                                                                                          'template_id',
                                                                                          'title',
                                                                                          'status',
                                                                                          'customer_id')
        templates = CouponTemplate.objects.filter(status=CouponTemplate.SENDING,
                                                  coupon_type=CouponTemplate.TYPE_TRANSFER).order_by("value").values(
            'id',
            'title',
            'value')

        templates_data = {
            50: [],
            100: [],
            150: [],
            200: [],
            300: [],
            400: [],
            'X': [],
        }
        for t in templates:
            if t['value'] <= 50:
                templates_data[50].append(t)
            elif t['value'] <= 100:
                templates_data[100].append(t)
            elif t['value'] <= 150:
                templates_data[150].append(t)
            elif t['value'] <= 200:
                templates_data[200].append(t)
            elif t['value'] <= 300:
                templates_data[300].append(t)
            elif t['value'] <= 400:
                templates_data[400].append(t)
            else:
                templates_data['X'].append(t)
        x = {'sale_orders': sale_orders,
             'time_from': time_from,
             'time_to': time_to,
             "templates_data": OrderedDict(
                 sorted(templates_data.items(), key=lambda templates_data: templates_data[0])),
             'buyer_id': buyer_id,
             'usercoupons': usercoupons,
             'model_ids': model_ids}
        return Response({'code': 0,
                         'info': 'success',
                         'data': x})

    def cancel_gift_coupon(self, usercoupon_id, action_user):
        # type:(int) -> bool
        """取消 赠送优惠券
        """
        from ..apis.v1.usercoupon import cancel_coupon_by_ids, get_user_coupon_by_id

        coupon = get_user_coupon_by_id(usercoupon_id)
        if not coupon or coupon.status != UserCoupon.UNUSED:
            raise Exception('优惠券不存在或者状态错误')
        order_no = 'gift-%s' % coupon.id
        record = CouponTransferRecord.objects.filter(order_no=order_no).first()
        if not record:
            raise Exception('优惠券流通记录不存在')

        with transaction.atomic():
            cancel_coupon_by_ids([usercoupon_id])
            record.set_transfer_status_cancel()

        log_action(action_user, coupon, CHANGE, u'取消优惠券，对应流通记录id为%s' % record.id)
        return True

    def post(self, request):
        content = request.POST
        customer = content.get('buyer_id', None)
        template_id = content.get('template_id', None)
        cancel_coupon_id = content.get('cancel_coupon_id', None)
        activity_id = content.get('activity_id', 0)
        activity_id = int(activity_id)
        if cancel_coupon_id:
            try:
                state = self.cancel_gift_coupon(int(cancel_coupon_id))
                info = '取消操作成功' if state else '取消失败'
            except Exception as e:
                info = e.message
                return Response({'code': 3, "info": info})
            return Response({'code': 0, "info": info})
        try:
            cus = Customer.objects.get(Q(mobile=customer) | Q(pk=customer), status=Customer.NORMAL)
        except:
            return Response({'code': 2, "info": '客户不存在或重复'})
        from ..apis.v1.transfer import create_present_coupon_transfer_record
        from ..apis.v1.transfercoupondetail import create_transfer_coupon_detail

        info = u'发送成功'
        try:
            from ..models.usercoupon import UserCoupon

            template = CouponTemplate.objects.get(id=template_id)
            unique_key = template.gen_usercoupon_unikey('gift_transfer_%s_%s' % (cus.id, activity_id), 1)
            if UserCoupon.objects.filter(uniq_id=unique_key).exists():
                return Response({'code': 1, "info": u'已经发送'})
            with transaction.atomic():
                cou, code, msg = create_user_coupon(cus.id, template.id, unique_key=unique_key)
                transf_record = create_present_coupon_transfer_record(cus, template, cou.id, uni_key_prefix=activity_id)
                create_transfer_coupon_detail(transf_record.id, [cou.id])

            log_action(request.user, cou, ADDITION, u'添加优惠券记录,对应精品券id为%s' % transf_record.id)
            log_action(request.user, transf_record, ADDITION, u'添加精品流通记录,对应优惠券id为%s' % cou.id)
        except Exception as e:
            info = e.message
        return Response({'code': 0, "info": info})


class VerifyReturnSysTransfer(APIView):
    transfer_coupons = CouponTransferRecord.objects.all()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)

    def post(self, request):
        # type: (HttpRequest) -> Response
        """工作人员 审核 用户申请的 退 精品优惠券
        """
        transfer_record_id = request.POST.get('transfer_record_id')
        return_func = request.POST.get('return_func')

        if not (transfer_record_id and return_func):
            return Response({'code': 1, 'info': '参数错误'})
        try:
            if return_func == 'agree':
                agree_apply_transfer_record_2_sys(transfer_record_id, user=request.user)
            elif return_func == 'reject':
                cancel_return_2_sys_transfer(transfer_record_id, admin_user=request.user)
            else:
                return Response({'code': 1, 'info': '参数错误'})
            return Response({'code': 0, 'info': '审核成功'})
        except Exception as e:
            return Response({'code': 2, 'info': '审核出错: %s' % e.message})
