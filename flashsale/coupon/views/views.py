# coding=utf-8
from __future__ import absolute_import, unicode_literals
from django.db import transaction
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response
from core.options import log_action, CHANGE, ADDITION
from flashsale.pay.models import SaleTrade, Customer
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
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "sale/release_usercoupon.html"
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)

    def get(self, request):
        content = request.GET
        buyer_id = content.get("buyer_id")
        model_ids = content.get("model_ids")
        time_from = content.get('time_from')
        time_to = content.get('time_to')
        sale_orders = []
        if buyer_id and model_ids:
            model_ids = [int(i.strip()) for i in model_ids.split(',') if i]
            from flashsale.pay.models import SaleOrder
            from shopback.items.models import Product

            item_ids = [i['id'] for i in Product.objects.filter(model_id__in=model_ids).values('id')]
            sale_orders = SaleOrder.objects.filter(item_id__in=item_ids, buyer_id=buyer_id,
                                                   status=SaleOrder.TRADE_FINISHED)
        if time_from:
            sale_orders = sale_orders.filter(pay_time__gte=time_from)
        if time_to:
            sale_orders = sale_orders.filter(pay_time__lte=time_to)
        templates = CouponTemplate.objects.filter(status=CouponTemplate.SENDING,
                                                  coupon_type=CouponTemplate.TYPE_TRANSFER).order_by("value")
        usercoupons = []
        if buyer_id:
            usercoupons = UserCoupon.objects.filter(customer_id=buyer_id, coupon_type=CouponTemplate.TYPE_TRANSFER)
        if time_from:
            usercoupons = usercoupons.filter(created__gte=time_from)
        if time_to:
            usercoupons = usercoupons.filter(created__lte=time_to)
        from flashsale.pay.models import ModelProduct

        default_modelids = ModelProduct.objects.filter(product_type=1, status=ModelProduct.NORMAL).values('id')
        default_modelids = ','.join([str(m['id']) for m in default_modelids])
        return Response({'sale_orders': sale_orders,
                         'time_from': time_from,
                         'time_to': time_to,
                         "templates": templates,
                         'usercoupons': usercoupons,
                         'default_modelids': default_modelids})

    def post(self, request):
        content = request.POST
        customer = content.get('buyer_id', None)
        template_id = content.get('template_id', None)
        activity_id = content.get('activity_id', 0)
        activity_id = int(activity_id)
        try:
            cus = Customer.objects.get(Q(mobile=customer) | Q(pk=customer), status=Customer.NORMAL)
        except:
            return Response({'code': 2, "message": '客户不存在或重复'})
        from ..apis.v1.transfer import create_present_coupon_transfer_record
        from ..apis.v1.transfercoupondetail import create_transfer_coupon_detail

        message = u'发送成功'
        try:
            from ..models.usercoupon import UserCoupon

            template = CouponTemplate.objects.get(id=template_id)
            unique_key = template.gen_usercoupon_unikey('gift_transfer_%s_%s' % (cus.id, activity_id), 1)
            if UserCoupon.objects.filter(uniq_id=unique_key).exists():
                return Response({'code': 0, "message": u'已经发送'})
            with transaction.atomic():
                cou, code, msg = create_user_coupon(cus.id, template.id, unique_key=unique_key)
                transf_record = create_present_coupon_transfer_record(cus, template, cou.id, uni_key_prefix=activity_id)
                create_transfer_coupon_detail(transf_record.id, transf_record.transfer_type, [cou.id])

            log_action(request.user, cou, ADDITION, u'添加优惠券记录,对应精品券id为%s' % transf_record.id)
            log_action(request.user, transf_record, ADDITION, u'添加精品流通记录,对应优惠券id为%s' % cou.id)
        except Exception as e:
            message = e.message
        return Response({'code': 0, "message": message})


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
