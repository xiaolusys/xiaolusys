# coding: utf-8

from django.views.generic import View
from django.shortcuts import HttpResponse, render, redirect
from django.template import RequestContext
from django.utils.safestring import mark_safe

from flashsale.pay.models import ModelProduct, Productdetail
from shopback.items.models import Product
from django.db import transaction
from core.options import log_action, ADDITION, CHANGE
from supplychain.supplier.models import SaleProduct


class AggregateProductView(View):
    def get(self, request, pk):
        from shopback.items.local_cache import rebeta_schema_cache

        schema_mapping = {i['id']:i['name'] for i in rebeta_schema_cache.schemas}
        s = SaleProduct.objects.filter(id=pk)

        all_product = Product.objects.filter(sale_product=pk, status=Product.NORMAL)
        #Todo: 给每个product设置misc
        for p in all_product:
            miscs = []
            miscs.append('<span>库存数：%s</span>' % p.collect_num)
            miscs.append('<span>预留数：%s</span>' % p.remain_num)
            miscs.append('<span>水印：%s</span>' % ('是' if p.is_watermark else '否', ))
            if hasattr(p, 'details'):
                miscs.append('<span>秒杀：%s</span>' % ('是' if p.details.is_seckill else '否', ))
                miscs.append('<span>专区推荐：%s</span>' % ('是' if p.details.is_recommend else '否', ))
                if p.details.rebeta_scheme_id:
                    schema = schema_mapping.get(p.details.rebeta_scheme_id) or ''
                    if schema:
                        miscs.append('<span>返利计划：%s</span>' % schema)
            p.misc = mark_safe('<br>'.join(miscs))
        return render(
            request,
            "aggregate_product.html",
              {"sale_product": s[0] if s.count() > 0 else None, "all_product": all_product},
        )

    @staticmethod
    @transaction.atomic
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



class GetProductView(View):
    def get(self, request):
        product_id = request.GET.get("product")
        s = SaleProduct.objects.filter(id=product_id)

        return render(
            request,
            "aggregate_product.html",
              {"sale_product": s[0] if s.count() > 0 else None},
        )
