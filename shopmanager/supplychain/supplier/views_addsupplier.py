# -*- encoding:utf8 -*-
from rest_framework import generics
from shopback.categorys.models import ProductCategory

from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response

from django.db import transaction

from shopback.base import log_action, ADDITION, CHANGE
from django.db.models import F, Q
from supplychain.supplier.models import SaleSupplier, SaleCategory, SaleProductManage, SaleProductManageDetail
import datetime
from supplychain.supplier.models import SaleProduct


class AddSupplierView(generics.ListCreateAPIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "add_supplier.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        platform_choice = SaleSupplier.PLATFORM_CHOICE
        process_choice = SaleSupplier.PROGRESS_CHOICES
        all_category = SaleCategory.objects.filter()
        return Response({"platform_choice": platform_choice, "all_category": all_category,
                         "process_choice": process_choice})

    @transaction.commit_on_success
    def post(self, request, *args, **kwargs):
        post = request.POST
        supplier_name = post.get("supplier_name")
        supplier_code = post.get("supplier_code", "")
        main_page = post.get("main_page", "")
        platform = post.get("platform")
        category = post.get("category")
        contact_name = post.get("contact_name")
        mobile = post.get("mobile")
        address = post.get("contact_address")
        memo = post.get("note")
        progress = post.get("progress")

        new_supplier = SaleSupplier(supplier_name=supplier_name, supplier_code=supplier_code, main_page=main_page,
                                    platform=platform, category_id=category, contact=contact_name, mobile=mobile,
                                    address=address, memo=memo, progress=progress)
        new_supplier.save()
        log_action(request.user.id, new_supplier, ADDITION, u'新建'.format(""))
        return Response({"supplier_id": new_supplier.id})


class CheckSupplierView(generics.ListCreateAPIView):
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        post = request.POST
        supplier_name = post.get("supplier_name", "")
        suppliers = SaleSupplier.objects.filter(supplier_name__contains=supplier_name)
        if suppliers.count() > 10:
            return Response({"result": "more"})
        if suppliers.count() > 0:
            return Response({"result": "10", "supplier": [s.supplier_name for s in suppliers]})
        return Response({"result": "0"})


from shopback.items.models import Product
from flashsale.pay.models_custom import ModelProduct, GoodShelf


def get_target_date_detail(target_date, category):
    target_sch = SaleProductManage.objects.filter(sale_time=target_date)
    try:
        end_time = target_date + datetime.timedelta(days=1)
    except:
        return "", "", ""
    try:
        goodshelf = GoodShelf.objects.get(active_time__range=(target_date, end_time))
        wem_posters_list = goodshelf.wem_posters
        if wem_posters_list:
            wem_posters = wem_posters_list[0]["pic_link"]
        chd_posters_list = goodshelf.chd_posters
        if chd_posters_list:
            chd_posters = chd_posters_list[0]["pic_link"]
    except:
        wem_posters = ""
        chd_posters = ""
    if target_sch.count() > 0:
        if category == "1":
            all_detail = target_sch[0].nv_detail
        elif category == "2":
            all_detail = target_sch[0].child_detail
        else:
            all_detail = target_sch[0].normal_detail
        return all_detail, wem_posters, chd_posters, target_sch[0]
    else:
        return "", wem_posters, chd_posters, []


class ScheduleManageView(generics.ListCreateAPIView):
    """* 排期管理界面 """
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    permission_classes = (permissions.IsAuthenticated,)
    template_name = "schedulemanage.html"

    def get(self, request, *args, **kwargs):
        target_date_str = request.GET.get("target_date", datetime.date.today().strftime("%Y-%m-%d"))
        category = request.GET.get("category", "0")
        result_data = []
        target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d')
        for i in range(0, 6):
            temp_date = target_date + datetime.timedelta(days=i)
            one_data, wem_posters, chd_posters, target_sch = get_target_date_detail(temp_date, category)
            result_data.append({"data": one_data, "date": temp_date.strftime("%Y-%m-%d"),
                                "wem_posters": wem_posters, "chd_posters": chd_posters})
        return Response({"result_data": result_data, "target_date": target_date_str, "category": category})


class ScheduleCompareView(generics.ListCreateAPIView):
    """排期比较"""
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    permission_classes = (permissions.IsAuthenticated,)
    template_name = "schedulecompare.html"

    def get(self, request, *args, **kwargs):
        target_date_str = request.GET.get("target_date", datetime.date.today().strftime("%Y-%m-%d"))
        target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d')
        try:
            end_time = target_date + datetime.timedelta(days=1)
        except:
            return "", "", ""
        lock_schedule = SaleProductManage.objects.filter(sale_time=target_date)
        if lock_schedule.count() == 0:
            return Response({"result": "0", "target_date": target_date_str})
        now_sachedule = SaleProduct.objects.filter(sale_time__gte=target_date, sale_time__lt=end_time,
                                                   status=SaleProduct.SCHEDULE)
        lock_list = set([one_product.sale_product_id for one_product in lock_schedule[0].normal_detail])
        now_list = set([one_product.id for one_product in now_sachedule])
        result_list = (lock_list | now_list) - (lock_list & now_list)
        return Response({"result_data": result_list, "target_date": target_date_str})


class SaleProductAPIView(generics.ListCreateAPIView):
    """
        *   get:获取每个选品的资料（库存、model、detail）
        *   post:
                -   type:1 设计接管选品
                -   type:2 排期完成，即设计组完成图片
    """
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        sale_product_id = request.GET.get("sale_product")
        if not sale_product_id:
            return Response({"flag": "error"})
        all_product = Product.objects.filter(status=Product.NORMAL, sale_product=sale_product_id)
        if all_product.count() == 0:
            return Response({"flag": "working"})
        color_list = all_product[0].details.color
        sku_list = ""
        for one_sku in all_product[0].normal_skus:
            sku_list += (one_sku.properties_alias + " | ")

        name = all_product[0].name.split("/")[0]
        lowest_price = all_product[0].lowest_price()
        std_sale_price = all_product[0].std_sale_price
        sale_charger = all_product[0].sale_charger
        model_id = all_product[0].model_id
        product_id = all_product[0].id
        single_model = True
        try:
            pmodel = ModelProduct.objects.get(id=all_product[0].model_id)
            if not pmodel.is_single_spec():
                model_id = pmodel.id
                single_model = False
            zhutu = pmodel.head_imgs.split()[0]
        except:
            try:
                zhutu = all_product[0].details.head_imgs.split()[0]
            except:
                zhutu = ""
        return Response({"flag": "done",
                         "color_list": color_list,
                         "sku_list": sku_list,
                         "name": name,
                         "zhutu": zhutu,
                         "lowest_price": lowest_price,
                         "std_sale_price": std_sale_price,
                         "sale_charger": sale_charger,
                         "model_id": model_id,
                         "single_model": single_model,
                         "product_id": product_id})

    def post(self, request, *args, **kwargs):
        detail = request.POST.get("detail_id")
        type = request.POST.get("type")
        try:
            detail_product = SaleProductManageDetail.objects.get(id=detail)
        except:
            return Response({"result": u"error"})
        if type == "1":
            if detail_product.design_take_over == SaleProductManageDetail.TAKEOVER:
                return Response({"result": u"alreadytakeover"})
            detail_product.design_person = request.user.username
            detail_product.design_take_over = SaleProductManageDetail.TAKEOVER
            detail_product.save()
            log_action(request.user.id, detail_product, CHANGE, u'接管')
            return Response({"result": u"success"})
        elif type == "2":
            if detail_product.design_complete:
                return Response({"result": u"alreadycomplete"})
            if detail_product.design_person != request.user.username:
                return Response({"result": u"not_same_people"})
            detail_product.design_complete = True
            detail_product.save()
            log_action(request.user.id, detail_product, CHANGE, u'完成')
            return Response({"result": u"success"})
        return Response({"result": u"error"})

