# -*- encoding:utf8 -*-
from django.views.generic import View
from django.shortcuts import HttpResponse, render_to_response, redirect
from django.template import RequestContext
from flashsale.pay.models_custom import ModelProduct, Productdetail
from shopback.items.models import Product
from django.db import transaction


class AggregateProductView(View):
    @staticmethod
    def get(request):
        return render_to_response("pay/aggregate_product.html", context_instance=RequestContext(request))

    @staticmethod
    @transaction.commit_on_success
    def post(request):
        post = request.POST
        m = ModelProduct()
        buy_limit = post.get("buy_limit", 0)

        m.name = post["product_name"]
        m.sale_time = post["df"]
        print buy_limit,"eeeeeeeeee"
        if buy_limit == "on":
            m.buy_limit = True
            m.per_limit = int(post.get("per_limit", 0))
        m.save()
        product_id_list = post.getlist("product_id")
        for product_id in product_id_list:
            pro = Product.objects.filter(id=product_id)
            if pro.count() > 0:
                temp_pro = pro[0]
                temp_pro.model_id = m.id
                temp_pro.save()
                all_details = Productdetail.objects.filter(product_id=product_id)
                head_imgs_str = ""
                content_imgs_str = ""
                for detail in all_details:
                    head_imgs_str = detail.head_imgs
                    content_imgs_str = detail.content_imgs
                if m.head_imgs != "":
                    m.head_imgs += "\n"
                    m.head_imgs += head_imgs_str
                else:
                    m.head_imgs += head_imgs_str
                m.content_imgs = content_imgs_str
                m.save()
        return redirect("/mm/add_aggregeta/?search_model=" + str(m.id))


class ModelProductView(View):
    @staticmethod
    def get(request):
        content = request.GET
        search_model = content.get('search_model', '0')
        all_model_product = ModelProduct.objects.all()
        if len(search_model) == 0:
            search_model = 0
        model_change = ModelProduct.objects.filter(id=search_model)
        all_product = None
        target_model = None
        if model_change.count() > 0:
            target_model = model_change[0]
            all_product = Product.objects.filter(model_id=model_change[0].id)
        return render_to_response("pay/aggregate_product2already.html",
                                  {"target_model": target_model, "all_product": all_product,"all_model_product":all_model_product},
                                  context_instance=RequestContext(request))

    @staticmethod
    def post(request):
        post = request.POST
        product_id_list = post.getlist("product_id")
        model_id = post.get("model_id", 0)
        m = ModelProduct.objects.get(id=model_id)
        all_model_product = ModelProduct.objects.all()
        for product_id in product_id_list:
            pro = Product.objects.filter(id=product_id)
            if pro.count() > 0:
                temp_pro = pro[0]
                temp_pro.model_id = m.id
                temp_pro.save()
                all_details = Productdetail.objects.filter(product_id=product_id)
                head_imgs_str = ""
                content_imgs_str = ""
                for detail in all_details:
                    print detail.head_imgs, "detail.head_imgs"
                    print detail.content_imgs, "detail.content_imgs"
                    head_imgs_str = detail.head_imgs
                    content_imgs_str = detail.content_imgs
                if m.head_imgs != "":
                    m.head_imgs += "\n"
                    m.head_imgs += head_imgs_str
                else:
                    m.head_imgs += head_imgs_str
                m.content_imgs = content_imgs_str
                m.save()
        all_product = Product.objects.filter(model_id=m.id)
        return render_to_response("pay/aggregate_product2already.html", {"target_model": m, "all_product": all_product,"all_model_product":all_model_product},
                                  context_instance=RequestContext(request))


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

