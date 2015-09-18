# -*- encoding:utf8 -*-
from django.views.generic import View
from django.shortcuts import HttpResponse, render_to_response, redirect
from django.template import RequestContext
from flashsale.pay.models_custom import ModelProduct, Productdetail
from shopback.items.models import Product
from django.db import transaction
from shopback.base import log_action, ADDITION, CHANGE
from supplychain.supplier.models import SaleProduct


class AggregateProductView(View):
    def get(self, request, pk):
        s = SaleProduct.objects.filter(id=pk)

        all_product = Product.objects.filter(sale_product=pk)
        return render_to_response("aggregate_product.html",
                                  {"sale_product": s[0] if s.count() > 0 else None, "all_product": all_product},
                                  context_instance=RequestContext(request))

    @staticmethod
    @transaction.commit_on_success
    def post(request, pk):
        post = request.POST
        product_id_list = post.getlist("product_id")
        for product_id in product_id_list:
            pro = Product.objects.filter(id=product_id)
            if pro.count() > 0:
                temp_pro = pro[0]
                temp_pro.sale_product = pk
                temp_pro.save()
                log_action(request.user.id, temp_pro, CHANGE, u'修改选品ID为{0}'.format(str(pk)))
        return redirect("/supplychain/supplier/bdproduct/" + str(pk))

