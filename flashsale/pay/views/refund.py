# -*- encoding:utf8 -*-
import collections
import datetime
from django.forms import model_to_dict
from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework import authentication
from rest_framework import exceptions
from core.options import log_action, CHANGE
from shopback.items.models import Product, ProductDaySale
from flashsale.pay.models import SaleRefund
from flashsale.pay import serializers
from ..apis.v1.refund import get_sale_refund_by_id, return_fee_by_refund_product, refund_postage, refund_coupon
from ..models import BudgetLog
import logging

logger = logging.getLogger(__name__)


class RefundReason(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "salerefund/refund_reason.html"

    def get(self, request):
        content = request.GET
        user_name = request.user.username
        today = datetime.datetime.today()
        pro_code = content.get("pro_code", None)
        pro_id = content.get("pro_id", None)
        if pro_code:
            pros = Product.objects.filter(outer_id=pro_code, status='normal')
        elif pro_id:
            pros = Product.objects.filter(id=pro_id, status='normal')
        else:
            return Response({'today': today, "user_name": user_name})
        if len(pros) > 0:
            pro = pros[0]
        else:
            return Response({'today': today, "user_name": user_name})

        if pro.model_id == 0 or pro.model_id is None:
            sale_refunds = SaleRefund.objects.filter(item_id=pro.id)
            sale = ProductDaySale.objects.filter(product_id=pro.id)
        else:
            pro_ids = Product.objects.filter(model_id=pro.model_id).values('id').distinct()
            sale_refunds = SaleRefund.objects.filter(item_id__in=pro_ids)
            sale = ProductDaySale.objects.filter(product_id__in=pro_ids)
        sale_num = sale.aggregate(total_sale=Sum('sale_num')).get("total_sale") or 0

        reason = {}
        des = []
        pro_info = model_to_dict(pro, fields=['name', 'pic_path', 'id'])
        for ref in sale_refunds:
            if reason.has_key(ref.reason):
                reason[ref.reason] += ref.refund_num
            else:
                reason[ref.reason] = ref.refund_num
            des.append(ref.desc)
        info_base = {'today': today, "user_name": user_name, "reason": reason, "sale_num": sale_num,
                     "desc": des, 'pro_info': pro_info}
        return Response(info_base)


class SaleRefundViewSet(viewsets.ModelViewSet):
    queryset = SaleRefund.objects.all()
    serializer_class = serializers.SaleRefundSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions, permissions.IsAdminUser)

    def destroy(self, request, *args, **kwargs):
        return Response({'code': 0, 'info': u'暂时为开放'})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('not allowed')

    @detail_route(methods=['post'])
    def refund_postage_manual(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> HttpResponse
        id = kwargs.get('pk')
        postage_num = request.POST.get('postage_num') or 0
        postage_num = int(postage_num) if postage_num.isdigit() else postage_num
        im_execute = request.POST.get('im_execute')
        im_execute = True if im_execute == u'true' else False
        default_return = collections.defaultdict(code=0, info='操作成功!')
        if BudgetLog.objects.get_refund_postage_budget_logs().filter(referal_id=id).exists():  # 该退款单的退货补邮费记录
            default_return.update({'code': 2, 'info': '已经有退货补邮费记录了'})
            return Response(default_return)
        sale_refund = get_sale_refund_by_id(id)
        refund_postage(sale_refund, postage_num=postage_num, im_execute=im_execute)
        return Response(default_return)

    @detail_route(methods=['post'])
    def refund_coupon_manual(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        id = kwargs.get('pk')
        im_execute = request.POST.get('im_execute')
        im_execute = True if im_execute == u'true' else False
        coupon_template_id = request.POST.get('coupon_template_id') or 0
        default_return = collections.defaultdict(code=0, info='操作成功!')
        if not coupon_template_id:
            default_return.update({'code': 1, 'info': '参数错误'})
            return Response(default_return)
        coupon_template_id = int(coupon_template_id)
        sale_refund = get_sale_refund_by_id(id)
        if sale_refund.get_refund_coupons().exists():
            default_return.update({'code': 2, 'info': '已经补发过了'})
            return Response(default_return)
        if coupon_template_id:
            amount_flow = sale_refund.amount_flow
            amount_flow.update({'refund_coupon': {
                'template_id': coupon_template_id,
                'send_status': False}})
            refund_coupon(sale_refund, amount_flow=amount_flow, im_execute=im_execute)
        return Response(default_return)
