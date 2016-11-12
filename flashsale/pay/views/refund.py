# -*- encoding:utf8 -*-
import datetime
from django.forms import model_to_dict
from django.db.models import Sum
from rest_framework.response import Response
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

import logging

logger = logging.getLogger(__name__)


class RefundReason(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "salerefund/refund_reason.html"

    def get(self, request):
        content = request.REQUEST
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
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        manual_refund = request.data.get('manual_refund')
        status = int(request.data.get('status'))
        if not instance.is_modifiable:
            raise exceptions.APIException(u'退款单当前状态不予更新退款单!')
        if instance.status == SaleRefund.REFUND_WAIT_RETURN_GOODS and \
                        status not in (SaleRefund.REFUND_WAIT_RETURN_GOODS,
                                       SaleRefund.REFUND_APPROVE,
                                       SaleRefund.REFUND_SUCCESS):
            raise exceptions.APIException(u'同意状态,不予修改状态!')
        if instance.status == SaleRefund.REFUND_WAIT_SELLER_AGREE and status == SaleRefund.REFUND_WAIT_RETURN_GOODS:
            instance.agree_return_goods()  # 如果是从退款待审　到　同意退货　则发送　退回信息
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        instance = self.queryset.filter(id=serializer.data.get('id')).first()
        message = u'审核退款单'
        if manual_refund == 'on':  # 开启手动退款
            instance.return_fee_by_refund_product()
            message = u'操作手动退款'
        log_action(request.user.id, instance, CHANGE, message)
        return Response(serializer.data)

