# -*- coding:utf-8 -*-

from django.shortcuts import redirect
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework import renderers

from core.options import log_action, ADDITION, CHANGE
from shopback.items.models import Product

import logging

logger = logging.getLogger('django.request')


class ProductInvalidConfirmView(APIView):
    #     authentication_classes = (authentication.TokenAuthentication,)
    #     permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer)
    template_name = "items/product_delete.html"

    def post(self, request):
        content = request.REQUEST
        product_ids = content.get('product_ids').split(',')
        origin_url = content.get('origin_url')

        product_qs = Product.objects.filter(outer_id__in=product_ids)
        for p in product_qs:
            # cnt = 0
            # success = False
            # invalid_outerid = p.outer_id
            # while cnt < 10:
            #     invalid_outerid += '_del'
            #     products = Product.objects.filter(outer_id=invalid_outerid)
            #     if products.count() == 0:
            #         success = True
            #         break
            #     cnt += 1
            # if not success:
            #     continue
            # p.outer_id = invalid_outerid
            p.status = Product.DELETE
            p.save()

            log_action(request.user.id, p, CHANGE, u'商品作废')

        messages.add_message(request._request, messages.INFO, u"已成功作废%s个商品!" % (len(product_ids)))

        return redirect(origin_url)
