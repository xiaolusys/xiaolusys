# coding=utf-8
from django.forms import model_to_dict
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.views import APIView
import datetime
from shopback.items.models import Product, ProductDaySale
from flashsale.pay.models_refund import SaleRefund
from django.db.models import Sum


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


class RefundAnaList(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "salerefund/pro_ref_list.html"

    def get(self, request):
        username = request.user.username
        return Response({"username": username})
