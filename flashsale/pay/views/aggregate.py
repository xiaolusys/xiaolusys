# -*- encoding:utf8 -*-
import datetime
from django.db import transaction
from django.forms.models import model_to_dict
from django.views.generic import View
from django.shortcuts import HttpResponse, render, redirect
from django.template import RequestContext

from rest_framework import generics
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response

from flashsale.pay.models import ModelProduct, Productdetail, ModelProduct
from shopback.items.models import Product
from supplychain.supplier.models import SaleProductManageDetail

from core.options import log_action, ADDITION, CHANGE

import logging

logger = logging.getLogger(__name__)


class AggregateProductView(View):
    @staticmethod
    def get(request):
        return render(
            request,
            "pay/aggregate_product.html"
        )

    @staticmethod
    @transaction.atomic
    def post(request):
        post = request.POST
        m = ModelProduct()
        buy_limit = post.get("buy_limit", 0)

        m.name = post["product_name"]
        m.sale_time = post["df"]
        m.head_imgs = post.get('head_img', '')
        m.content_imgs = post.get('content_img', '')
        if buy_limit == "on":
            m.buy_limit = True
            m.per_limit = int(post.get("per_limit", 0))
        m.save()
        log_action(request.user.id, m, ADDITION, u'新建款式')
        product_id_list = post.getlist("product_id")
        for product_id in product_id_list:
            product = Product.objects.filter(id=product_id).first()
            if product:
                color_name = product.name.find('/') >= 0 and product.name.split('/')[1] or ''
                product.name = '%s/%s'%(m.name , color_name)
                product.model_id = m.id
                product.save(update_fields=['name','model_id'])
                log_action(request.user.id, product, CHANGE, u'聚合商品到{0}'.format(m.id))
        return redirect("/mm/aggregeta_product/")


class ModelProductView(View):
    """
        *   get:款式商品列表，根据款式的id进行搜索，找出相关联的库存商品
        *   post:将搜索出来的商品，关联到某个款式
    """

    @staticmethod
    def get(request):
        content = request.GET
        search_model = content.get('search_model', '0')
        all_model_product = ModelProduct.objects.exclude(status=u'1').order_by('-created')[0:20]
        if len(search_model) == 0:
            search_model = 0
        model_change = ModelProduct.objects.filter(id=search_model)
        all_product = None
        target_model = None
        content_img = None
        if model_change.count() > 0:
            target_model = model_change[0]
            all_product = Product.objects.filter(model_id=model_change[0].id, status__in=(Product.NORMAL,Product.REMAIN))
            content_img = model_change[0].content_imgs.split()
        return render(
            request,
            "pay/aggregate_product2already.html",
              {"target_model": target_model, "all_product": all_product,
               "all_model_product": all_model_product, "content_img": content_img},
        )

    @staticmethod
    def post(request):
        post = request.POST
        product_id_list = post.getlist("product_id")
        model_id = post.get("model_id", 0)
        m = ModelProduct.objects.get(id=model_id)
        all_model_product = ModelProduct.objects.exclude(status=u'1').order_by('-created')[0:20]
        for product_id in product_id_list:
            pro = Product.objects.filter(id=product_id)
            if pro.count() > 0:
                temp_pro = pro[0]
                temp_pro.model_id = m.id
                temp_pro.save()
                log_action(request.user.id, temp_pro, CHANGE, u'修改款式ID为{0}'.format(model_id))
        all_product = Product.objects.filter(model_id=m.id)
        return render(
            request,
            "pay/aggregate_product2already.html",
            {"target_model": m, "all_product": all_product,
              "all_model_product": all_model_product},
        )


class CheckModelExistView(View):
    @staticmethod
    def get(request):
        product_name = request.GET.get("product_name", "")
        m_pro = ModelProduct.objects.filter(name=product_name, status='0')
        if m_pro.count() > 0:
            result_str = """{"result":true}"""
        else:
            result_str = """{"result":false}"""
        return HttpResponse(result_str)

def check_aggregate_error(product):
    p_outer_id = product.outer_id
    outer_jie = p_outer_id[0:len(p_outer_id) - 1]
    p_model_id = product.model_id
    agg_products = Product.objects.filter(outer_id__contains=outer_jie, status=Product.NORMAL)
    for agg_product in agg_products:
        if agg_product.model_id != p_model_id:
            return True
    return False


def check_one_model(product):
    p_outer_id = product.outer_id
    outer_jie = p_outer_id[0:len(p_outer_id) - 1]
    agg_products = Product.objects.filter(outer_id__contains=outer_jie, status=Product.NORMAL)
    return agg_products.count() == 1


class AggregateProductCheckView(View):
    @staticmethod
    def get(request):
        product_res = []
        sale_time = request.GET.get("sale_time", datetime.date.today())
        all_prodcut = Product.objects.filter(sale_time=sale_time, status=Product.NORMAL)
        for product in all_prodcut:
            product_dict = model_to_dict(product)
            product_dict['error_tip'] = check_aggregate_error(product)
            if product.model_id == 0:
                product_dict['model_product'] = "0"
            else:
                m_product = ModelProduct.objects.filter(id=product.model_id)

                if m_product.count() > 0:
                    product_dict['model_product'] = model_to_dict(m_product[0])
                else:
                    product_dict['model_product'] = "0"
            product_res.append(product_dict)
            product_res.sort()
        return render(
            request,
            "pay/check_product.html",
            {"all_product": product_res, "sale_time": sale_time}
        )

    @staticmethod
    def post(request):
        post = request.POST
        return render(
            request,
            "pay/check_product.html",
        )


class ChuanTuAPIView(generics.ListCreateAPIView):
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        type = request.POST.get("type")
        pro_id = request.POST.get("pro_id")
        pic_link = request.POST.get("pic_link")
        coverage = request.POST.get("coverage")
        if type == "1":
            try:
                model_product = ModelProduct.objects.get(id=pro_id)
                model_product.head_imgs = pic_link
                model_product.save()
                log_action(request.user.id, model_product, CHANGE, u'上传头图')
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
                return Response({"result": u"error"})
        elif type == "3":
            try:
                product = Product.objects.get(id=pro_id)
                model_product = ModelProduct.objects.filter(id=product.model_id).first()
                detail, status = Productdetail.objects.get_or_create(product=product)
                detail.head_imgs = pic_link
                detail.save()
                product.pic_path = pic_link
                product.save()
                log_action(request.user.id, product, CHANGE, u'上传图片')
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
                return Response({"result": u"error"})
        elif type == "2":
            try:
                model_product = ModelProduct.objects.get(id=pro_id)
                if coverage == "true":
                    model_product.content_imgs += "\n" + pic_link
                else:
                    model_product.content_imgs = pic_link
                model_product.save()
                # 同步同款所有的商品detail
                log_action(request.user.id, model_product, CHANGE, u'上传内容图')
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
                return Response({"result": u"error"})
        else:
            logger.error('不在参数范围', exc_info=True)
            return Response({"result": u"error"})

        if model_product and model_product.head_imgs.strip() and model_product.content_imgs.strip():
            SaleProductManageDetail.objects.set_design_complete_by_saleproduct(model_product.saleproduct)

        return Response({"result": u"success"})


class ModelChangeAPIView(generics.ListCreateAPIView):
    """
        *   post:
                -   type:1 修改model的名字和关联的库存商品名

    """
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        model_id = request.POST.get("model_id")
        model_name = request.POST.get("model_name")
        try:
            model_bean = ModelProduct.objects.get(id=model_id)
            model_bean.name = model_name
            model_bean.save()
            for product in model_bean.products:
                color_name = product.name.find('/') >= 0 and product.name.split('/')[1] or ''
                product.name = '%s/%s'%(model_name, color_name)
                product.save(update_fields=['name'])
            log_action(request.user.id, model_bean, CHANGE, u'修改名字')
            products = Product.objects.filter(status=Product.NORMAL, model_id=model_bean.id)
            change_name(request.user.id, model_name, products)
        except:
            return Response({"flag": "error"})
        return Response({"flag": "done"})


def change_name(userid, name, products):
    for product in products:
        product_name = product.name
        if len(product_name.split("/")) > 1:
            product.name = name + "/" + product_name.split("/")[1]
            product.save()
            log_action(userid, product, CHANGE, u'修改名字')
            continue
        if len(product_name.split("-")) > 1:
            product.name = name + "/" + product_name.split("-")[1]
            product.save()
            log_action(userid, product, CHANGE, u'修改名字')
