# coding:utf-8
from django.db import transaction

from rest_framework import generics
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response

from shopback.categorys.models import ProductCategory
from shopback.items.models import Product, ProductSku, ProductSkuContrast, ContrastContent
from flashsale.pay.models_custom import ModelProduct, Productdetail
from flashsale.xiaolumm.models_rebeta import AgencyOrderRebetaScheme
from supplychain.supplier.models import SaleSupplier
from shopback.base import log_action, ADDITION, CHANGE
from django.db.models import F, Q
from supplychain.supplier.models import SaleProduct
from flashsale.pay.signals import signal_record_supplier_models


class AddItemView(generics.ListCreateAPIView):
    queryset = ProductCategory.objects.all()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "items/add_item.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return Response({"v": "v"})

    # @transaction.commit_on_success
    def post(self, request, *args, **kwargs):
        """ 新增库存商品　新增款式
        """
        content = request.data
        user = request.user

        product_name = content.get("product_name", "")
        category = content.get("category", "")
        shelf_time = content.get("shelf_time", "")
        material = content.get("material", "")
        note = content.get("note", "")
        wash_instroduce = content.get("wash_instroduce", "")
        header_img = content.get("header_img", "")
        ware_by = content.get("ware_by", "")
        supplier = content.get("supplier", "")
        saleproduct = content.get("saleproduct", "")
        sale_product = SaleProduct.objects.filter(id=saleproduct)
        if sale_product.count() == 0 or str(sale_product[0].sale_supplier.id) != supplier:
            return Response({"result": "选品ID错误"})
        if product_name == "" or category == "" or wash_instroduce == "" \
                or shelf_time == "" or material == "" or supplier == "" \
                or header_img == "" or ware_by == "":
            return Response({"result": "填写表单错误"})
        category_item = ProductCategory.objects.get(cid=category)
        if category_item.parent_cid == 5:
            first_outer_id = u"9"
            outer_id = first_outer_id + str(category_item.cid) + "%05d" % int(supplier)
        elif category_item.parent_cid == 8:
            first_outer_id = u"8"
            outer_id = first_outer_id + str(category_item.cid) + "%05d" % int(supplier)
        elif category_item.cid == 9:
            outer_id = "100" + "%05d" % int(supplier)
        else:
            return Response({"result": "类别错误"})

        count = 1
        while True:
            inner_outer_id = outer_id + "%03d" % count
            test_pros = Product.objects.filter(outer_id__startswith=inner_outer_id)
            if test_pros.count() == 0 or count > 998:
                break
            count += 1
        if len(inner_outer_id) > 12:
            return Response({"result": "编码生成错误"})
        model_pro = ModelProduct(name=product_name, head_imgs=header_img, sale_time=shelf_time)
        model_pro.save()
        log_action(user.id, model_pro, ADDITION, u'新建一个modelproduct new')
        all_colors = content.get("all_colors", "").split(",")
        all_sku = content.get("all_sku", "").split(",")
        chi_ma_str = content.get("all_chima", "")
        all_chi_ma = [] if content.get("all_chima", "") == "" else chi_ma_str.split(",")
        chi_ma_result = {}
        for sku in all_sku:
            for chi_ma in all_chi_ma:
                temp_chi_ma = ContrastContent.objects.get(name=chi_ma)
                chi_ma_content = content.get(sku + "_" + chi_ma + "_size")
                if chi_ma_content and len(chi_ma_content) > 0 and chi_ma_content != "0":
                    if sku in chi_ma_result:
                        chi_ma_result[sku][temp_chi_ma.id] = chi_ma_content
                    else:
                        chi_ma_result[sku] = {temp_chi_ma.id: chi_ma_content}
        pro_count = 1
        for color in all_colors:
            total_remain_num = 0
            for sku in all_sku:
                remain_num = content.get(color + "_" + sku + "_remainnum", "")
                cost = content.get(color + "_" + sku + "_cost", "")
                price = content.get(color + "_" + sku + "_pricestd", "")
                agentprice = content.get(color + "_" + sku + "_agentprice", "")
                total_remain_num += int(remain_num)

            one_product = Product(name=product_name + "/" + color, outer_id=inner_outer_id + str(pro_count),
                                  model_id=model_pro.id, sale_charger=user.username,
                                  category=category_item, remain_num=total_remain_num, cost=cost,
                                  agent_price=agentprice, std_sale_price=price, ware_by=int(ware_by),
                                  sale_time=shelf_time, pic_path=header_img, sale_product=saleproduct)
            one_product.save()
            log_action(user.id, one_product, ADDITION, u'新建一个product_new')
            pro_count += 1
            one_product_detail = Productdetail(product=one_product, material=material,
                                               color=content.get("all_colors", ""),
                                               wash_instructions=wash_instroduce, note=note)
            one_product_detail.save()
            chima_model = ProductSkuContrast(product=one_product, contrast_detail=chi_ma_result)
            chima_model.save()
            count = 1
            for sku in all_sku:
                outer_id = content.get(color + "_" + sku + "_outerid", "")
                remain_num = content.get(color + "_" + sku + "_remainnum", "")
                cost = content.get(color + "_" + sku + "_cost", "")
                price = content.get(color + "_" + sku + "_pricestd", "")
                agentprice = content.get(color + "_" + sku + "_agentprice", "")
                one_sku = ProductSku(outer_id=outer_id, product=one_product, remain_num=remain_num, cost=cost,
                                     std_sale_price=price, agent_price=agentprice,
                                     properties_name=sku, properties_alias=sku)
                one_sku.save()
                log_action(user.id, one_sku, ADDITION, u'新建一个sku_new')
                count += 1
        # 发送　添加供应商总选款的字段　的信号
        signal_record_supplier_models.send(sender=ModelProduct, obj=model_pro)
        return Response({"result": "OK", "outer_id": inner_outer_id})


class GetCategory(generics.ListCreateAPIView):
    queryset = ProductCategory.objects.filter(status=ProductCategory.NORMAL)
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        result_data = {}

        root_category = self.queryset.filter(parent_cid=0)
        temp = {}
        for category in root_category:
            temp[category.cid] = category.name
            child_category = self.queryset.filter(parent_cid=category.cid)
            child_temp = {}
            for c_category in child_category:
                child_temp[c_category.cid] = c_category.name
                third_child_category = self.queryset.filter(parent_cid=c_category.cid)
                third_temp = {}
                for t_category in third_child_category:
                    third_temp[t_category.cid] = t_category.name
                if third_child_category.count() > 0:
                    result_data["0," + str(category.cid) + "," + str(c_category.cid)] = third_temp
            result_data["0," + str(category.cid)] = child_temp
        result_data['0'] = temp
        return Response(result_data)


class GetSupplier(generics.ListCreateAPIView):
    queryset = SaleSupplier.objects.filter(status=SaleSupplier.CHARGED)
    renderer_classes = (JSONRenderer,)

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        result_data = {}
        supplier_id = request.GET.get("supplier_id", "0")
        all_supplier = self.queryset
        if supplier_id != "0":
            all_supplier = all_supplier.filter(id=supplier_id)
        for supplier in all_supplier:
            result_data[supplier.id] = supplier.supplier_name
        return Response({"0": result_data})


class GetSkuDetail(generics.ListCreateAPIView):
    """
        展示某个商品的所有的sku详情尺码
    """
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    permission_classes = (permissions.IsAuthenticated,)
    template_name = "items/change_chima.html"

    def get(self, request, *args, **kwargs):
        content = request.GET
        searchtext = content.get("search_input")
        if not searchtext or len(searchtext.strip()) == 0:
            return Response({"result": "NOTFOUND"})
        product_bean = Product.objects.filter(Q(outer_id=searchtext))
        all_chima_content = ContrastContent.objects.all().order_by('sid')
        try:
            if product_bean.count() > 0:
                all_sku = [key.properties_alias for key in product_bean[0].normal_skus]
                result_data = {}
                for one_sku in all_sku:
                    notexist_skus = []
                    for one_chima in all_chima_content:
                        try:
                            contrast_detail = product_bean[0].contrast.contrast_detail
                            if one_sku in contrast_detail:
                                chi_ma_size = contrast_detail[one_sku][one_chima.cid]
                            else:
                                chi_ma_size = 0
                        except:
                            chi_ma_size = 0
                            notexist_skus.append((one_chima.name, chi_ma_size))
                            continue
                        if one_sku in result_data:
                            result_data[one_sku].append((one_chima.name, chi_ma_size))
                        else:
                            result_data[one_sku] = [(one_chima.name, chi_ma_size)]
                    result_data[one_sku].extend(notexist_skus)
                # chima_content = product_bean[0].contrast.get_correspond_content
                chima_content = result_data.items()
                chima_content.sort(cmp=custom_sort)
                return Response({"result": chima_content, "product_id": product_bean[0].id, "searchtext": searchtext})
            else:
                return Response({"result": "NOTFOUND", "searchtext": searchtext})
        except:
            return Response({"result": "NOTFOUND", "product_id": product_bean[0].id, "searchtext": searchtext})

    def post(self, request, *args, **kwargs):
        content = request.POST
        user = request.user
        product = content.get("product")
        product_bean = Product.objects.filter(id=product, status=Product.NORMAL)
        if product_bean.count() == 0:
            return Response({"result": "error"})
        product_model = product_bean[0]
        all_sku = [key.properties_alias for key in product_model.normal_skus]
        all_chi_ma = set()
        for k, v in content.items():
            if len(k.split("_")) == 3:
                all_chi_ma.add(k.split("_")[2])
        chi_ma_result = {}
        for sku in all_sku:
            for chi_ma in all_chi_ma:
                temp_chi_ma = ContrastContent.objects.get(name=chi_ma)
                chi_ma_content = content.get(str(product_model.id) + "_" + sku + "_" + chi_ma)
                if chi_ma_content and len(chi_ma_content) > 0 and chi_ma_content != "0":
                    if sku in chi_ma_result:
                        chi_ma_result[sku][temp_chi_ma.id] = chi_ma_content
                    else:
                        chi_ma_result[sku] = {temp_chi_ma.id: chi_ma_content}
        try:
            product_model.contrast.contrast_detail = chi_ma_result
            product_model.contrast.save()
            log_action(user.id, product_model, CHANGE, u'修改尺码表内容')
        except:
            chima_model = ProductSkuContrast(product=product_model, contrast_detail=chi_ma_result)
            chima_model.save()
            log_action(user.id, product_model, ADDITION, u'新建尺码表内容')
        return Response({"result": "OK"})


class PreviewSkuDetail(generics.ListCreateAPIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    permission_classes = (permissions.IsAuthenticated,)
    template_name = "items/preview_chima.html"

    def get(self, request, *args, **kwargs):
        content = request.GET
        searchtext = content.get("search_input")
        if not searchtext or len(searchtext.strip()) == 0:
            return Response({"result": "NOTFOUND"})
        product_bean = Product.objects.filter(Q(outer_id=searchtext) | Q(id=searchtext)).filter(status=Product.NORMAL)
        try:
            if product_bean.count() > 0:
                chima_content = product_bean[0].contrast.get_correspond_content
                chima_content = chima_content.items()
                chima_content.sort(cmp=custom_sort)
                return Response({"result": chima_content, "product_id": product_bean[0].id, "searchtext": searchtext})
            else:
                return Response({"result": "NOTFOUND", "searchtext": searchtext})
        except:
            return Response({"result": "NOTFOUND", "product_id": product_bean[0].id, "searchtext": searchtext})


def custom_sort(a, b):
    if a[0].isdigit() and b[0].isdigit():
        return int(a[0]) - int(b[0])

    if a[0].isdigit() and not b[0].isdigit():
        return True

    if not a[0].isdigit() and b[0].isdigit():
        return False

    return len(a[0]) - len(b[0]) or a[0] > b[0]


import datetime


class BatchSetTime(generics.ListCreateAPIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    permission_classes = (permissions.IsAuthenticated,)
    template_name = "items/batch_settime.html"

    def get(self, request, *args, **kwargs):
        content = request.GET
        target_shelf_date = content.get("shelf_date", datetime.date.today())
        model_id = content.get("model_id", '')
        p_cate_search = content.get("search_cate", None)
        ex_names = ['小鹿美美', '优尼世界']
        parent_categorys = ProductCategory.objects.filter(is_parent=True).exclude(name__in=ex_names)
        p_cates = []
        for parent in parent_categorys:
            p_kv = {"p_cid": parent.cid, "p_fullcate_name": parent.__unicode__()}
            p_cates.append(p_kv)
        categorys = ProductCategory.objects.filter(is_parent=False)
        if model_id is not None and "-" in model_id:
            model_id_strip = model_id.strip()
            models = model_id_strip.split('-')
        elif model_id == "" or model_id is None:
            models = []
            model_id_strip = ''
        else:
            model_id_strip = model_id.strip()
            models = [model_id_strip, ]
        # 添加类目
        cates = []
        for cate in categorys:
            kv = {"cid": cate.cid, "full_cate_name": cate.__unicode__()}
            cates.append(kv)
        if models and len(models) != 0:
            products = Product.objects.filter(model_id__in=models, status=Product.NORMAL).order_by("outer_id")
        elif p_cate_search is not None and p_cate_search != "":
            products = Product.objects.filter(sale_time=target_shelf_date, status=Product.NORMAL
                                              , category__parent_cid=p_cate_search).order_by("outer_id")
        else:
            products = []
        rebeta_schemes = AgencyOrderRebetaScheme.objects.filter(status=AgencyOrderRebetaScheme.NORMAL)
        print 'debug:',rebeta_schemes
        return Response({"all_product": products, 
                         "model_id":model_id,
                         "target_shelf_date": target_shelf_date, 
                         "cates": cates,
                         "ware_by": Product.WARE_CHOICES, 
                         "rebeta_schemes":rebeta_schemes,
                         "p_cates": p_cates})

    def add_kill_title(self, pros, actioner):
        """ 添加秒杀标题 """
        for pro in pros:
            title = pro.title()
            if not title.startswith('秒杀'):  # 防止重复添加秒杀
                pro.name = '秒杀 ' + title
                # 添加备注　秒杀不退不换
                pro.memo += u'秒杀商品，一经售出，概不退换'
                pro.save()
                log_action(actioner, pro, CHANGE, u'批量添加秒杀标题')
        return

    def remove_kill_title(self, pros, actioner):
        """ 移除秒杀标题 """
        for pro in pros:
            title = pro.title()
            if not title.startswith('秒杀'): continue  # 不是秒杀开头则不处理
            no_kill_title = title.replace("秒杀", "").lstrip()
            pro.name = no_kill_title
            no_kill_memo = pro.memo.replace(u'秒杀商品，一经售出，概不退换', u'')
            pro.memo = no_kill_memo
            pro.save()
            log_action(actioner, pro, CHANGE, u'批量删除秒杀标题')
        return

    @transaction.commit_on_success
    def post(self, request, *args, **kwargs):
        content = request.POST
        target_product = content.get("product_list", None)
        add_kill_title = content.get("add_kill_title", None)
        all_product = target_product.split(",")
        pros = Product.objects.filter(id__in=all_product)
        if add_kill_title is not None and int(add_kill_title) == 1:  # 添加秒杀标题
            self.add_kill_title(pros, request.user.id)
        elif add_kill_title is not None and int(add_kill_title) == 0:  # 移除秒杀
            self.remove_kill_title(pros, request.user.id)
        for pro in pros:
            properties = []
            for k, v in request.data.iteritems():
                k = str(k)
                if k in ("offshelf_time", "sale_time", "ware_by", "agent_price") and v == "": continue
                if hasattr(pro, k):
                    if k == 'is_watermark':
                        setattr(pro, k, int(v))
                    else:
                        setattr(pro, k, v)
                    properties.append((Product._meta.get_field(k).verbose_name.title(),v))
                
                if k == 'agent_price':
                    pro.pskus.update(agent_price=v)
                if k == 'rebeta_scheme_id' and v != '':
                    product_detail,state = Productdetail.objects.get_or_create(product=pro)
                    product_detail.rebeta_scheme_id = v
                    product_detail.save()
                    properties.append((Productdetail._meta.get_field(k).verbose_name.title(),v))
            pro.save()
            if k:log_action(request.user.id, pro, CHANGE, u'批量设置产品:%s'%(','.join('%s＝%s'%p for p in properties)))
        return Response({"code": 0})

