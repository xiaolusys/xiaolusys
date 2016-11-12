# coding=utf-8
from django.views.generic import View
from django.http import HttpResponse
import json
from supplychain.supplier.models import SaleProduct, HotProduct


class HotProductView(View):
    def post(self, request):
        content = request.POST
        sale_id = content.get("sale_id", None)

        sale_pro = SaleProduct.objects.get(id=sale_id)

        title = sale_pro.title or ' '
        pic_url = sale_pro.pic_url or ' '
        product_link = sale_pro.product_link or ' '
        price = sale_pro.on_sale_price  # 售价
        user = request.user.id

        try:
            hot_pro = HotProduct.objects.get(proid=sale_id)
            hot_pro.name = title
            hot_pro.pic_pth = pic_url
            hot_pro.site_url = product_link
            hot_pro.price = price
            hot_pro.contactor = user
            hot_pro.save()
            # 保存字段信息
            status = {"code": 1}  # 原来有产品　修改该字段成功
        except HotProduct.DoesNotExist:
            hot_pro = HotProduct.objects.create(name=title, proid=sale_id, pic_pth=pic_url, site_url=product_link,
                                                price=price, contactor=user)
            status = {"code": 2}  # 原来没有产品　创建产品成功
        return HttpResponse(json.dumps(status), content_type='application/json')

