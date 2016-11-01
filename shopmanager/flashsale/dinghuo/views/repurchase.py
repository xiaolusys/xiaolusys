# coding:utf-8
"""
    补单进货
"""
import re
from django.db.models import *
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, renderers, viewsets
from flashsale.dinghuo.models import OrderList
from rest_framework.response import Response


class RePurchaseViewSet(viewsets.GenericViewSet):
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer, renderers.BrowsableAPIRenderer)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = OrderList.objects.filter(created_by=OrderList.CREATED_BY_REPURCHASE)

    def create(self, request, pk=None):
        result = {}
        ol = get_object_or_404(OrderList, pk=pk)
        sku_ids = request.GET.get('sku_ids', '')
        product_ids = request.GET.get('product_ids', '')

        user = request.user
        orderDrAll = OrderDraft.objects.all().filter(buyer_name=user)
        productres = []
        for p in queryset:
            product_dict = model_to_dict(p)
            product_dict['prod_skus'] = []
            guiges = ProductSku.objects.filter(product_id=p.id).exclude(
                status=u'delete')
            for guige in guiges:
                sku_dict = model_to_dict(guige)
                sku_dict['name'] = guige.name
                sku_dict[
                    'wait_post_num'] = functions2view.get_lack_num_by_product(
                    p, guige)
                product_dict['prod_skus'].append(sku_dict)
            productres.append(product_dict)
        return render_to_response("dinghuo/addpurchasedetail.html",
                                  {"productRestult": productres,
                                   "drafts": orderDrAll},
                                  context_instance=RequestContext(request))

        return Response(result, template_name='dinghuo/purchase/purchase.html')

    def create(self, request, pk=None):
        result = {}
        return Response(result, template_name='dinghuo/inbound.html')