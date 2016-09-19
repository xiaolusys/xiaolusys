# coding:utf-8
import datetime
import json
import logging
import urllib

from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.utils.safestring import mark_safe
from rest_framework import exceptions
from rest_framework import generics
from rest_framework import permissions
from rest_framework.decorators import list_route
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response

from common import page_helper
from core.options import log_action, ADDITION, CHANGE
from flashsale.pay.models import ModelProduct, Productdetail, default_modelproduct_extras_tpl
from flashsale.pay.signals import signal_record_supplier_models
from flashsale.xiaolumm.models.models_rebeta import AgencyOrderRebetaScheme
from shopback.categorys.models import ProductCategory
from shopback.items import constants, forms, local_cache
from shopback.items.models import (Product, ProductSku, ProductSchedule,
                                   ProductSkuContrast, ContrastContent,
                                   ProductSkuStats)
from supplychain.supplier.models import SaleSupplier, SaleProduct
from shopback.warehouse import WARE_NONE, WARE_GZ, WARE_SH, WARE_CHOICES
logger = logging.getLogger(__name__)


class AddItemView(generics.ListCreateAPIView):
    queryset = ProductCategory.objects.all()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return Response({"v": "v"}, template_name='items/add_item.html')

    @list_route(methods=['get'])
    def health(self, request, *args, **kwargs):
        return Response({"v": "v"}, template_name='items/add_item_health.html')

    # @transaction.atomic
    def post(self, request, *args, **kwargs):
        """ 新增库存商品　新增款式 """
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
        saleproduct_id = content.get("saleproduct", "")
        saleproduct = SaleProduct.objects.filter(id=saleproduct_id).first()
        if not saleproduct:
            return Response({"result": u"选品ID错误"})
        supplier = saleproduct.sale_supplier.id
        category_item = ProductCategory.objects.get(cid=category)
        category_maps = {
            3: '3',
            39: '3',
            6: '6',
            5: '9',
            52: '5',
            44: '7',
            8: '8',
            49: '4',
        }
        if category_maps.has_key(category_item.parent_cid):
            outer_id = category_maps.get(category_item.parent_cid) + str(category_item.cid) + "%05d" % supplier
        elif category_item.cid == 9:
            outer_id = "100" + "%05d" % supplier
        else:
            return Response({"result": "请补全三级类目信息"})

        count = Product.objects.filter(outer_id__startswith=outer_id).count() or 1
        while True:
            inner_outer_id = outer_id + "%03d" % count
            product_ins = Product.objects.filter(outer_id__startswith=inner_outer_id).first()
            if not product_ins or count > 998:
                break
            count += 1
        if len(inner_outer_id) > 12:
            return Response({"result": "编码生成错误"})

        extras = default_modelproduct_extras_tpl()
        extras.setdefault('properties', {})
        for key in ('note', 'wash_instroduce', 'material', 'all_colors', 'fashion'):
            value = content.get(key)
            if value:
                if key == 'all_colors': key='color'
                extras['properties'][key] = value
        # TODO@meron 考虑到亲子装问题，支持同一saleproduct录入多个modelproduct
        model_pro = ModelProduct(
            name=product_name,
            head_imgs=header_img,
            salecategory=saleproduct.sale_category,
            saleproduct=saleproduct,
            is_flatten=False,
            lowest_agent_price=round(min([float(v) for k,v in content.items() if k.endswith('_agentprice')]), 2),
            lowest_std_sale_price=round(min([float(v) for k,v in content.items() if k.endswith('_pricestd')]),2),
            extras=extras,
        )
        model_pro.save()
        log_action(user.id, model_pro, ADDITION, u'新建一个modelproduct new')
        all_colors = content.get("all_colors", "").split(",")
        all_sku = content.get("all_sku", "").split(",")
        chi_ma_str = content.get("all_chima", "")
        all_chi_ma = [] if content.get("all_chima", "") == "" else chi_ma_str.split(",")
        chi_ma_result = {}
        for sku in all_sku:
            for chi_ma in all_chi_ma:
                temp_chi_ma, state = ContrastContent.objects.get_or_create(name=chi_ma)
                chi_ma_content = content.get(sku + "_" + chi_ma + "_size")
                if chi_ma_content and len(chi_ma_content) > 0 and chi_ma_content != "0":
                    if sku in chi_ma_result:
                        chi_ma_result[sku][temp_chi_ma.cid] = chi_ma_content
                    else:
                        chi_ma_result[sku] = {temp_chi_ma.cid: chi_ma_content}
        pro_count = 1
        for color in all_colors:
            total_remain_num = 0
            for sku in all_sku:
                remain_num = content.get(color + "_" + sku + "_remainnum", "")
                cost = content.get(color + "_" + sku + "_cost", "")
                price = content.get(color + "_" + sku + "_pricestd", "")
                agentprice = content.get(color + "_" + sku + "_agentprice", "")
                total_remain_num += int(remain_num)
            # product除第一个颜色外, 其余的颜色的outer_id末尾不能为1
            if (pro_count % 10) == 1 and pro_count > 1:
                pro_count += 1
            try:
                one_product = Product(name=product_name + "/" + color, outer_id=inner_outer_id + str(pro_count),
                                      model_id=model_pro.id, sale_charger=user.username,
                                      category=category_item, remain_num=total_remain_num, cost=cost,
                                      agent_price=agentprice, std_sale_price=price, ware_by=int(ware_by),
                                      pic_path=header_img, sale_product=saleproduct.id)
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
                    barcode = one_product.outer_id + str(count)
                    outer_id = barcode
                    remain_num = content.get(color + "_" + sku + "_remainnum", "")
                    cost = content.get(color + "_" + sku + "_cost", "")
                    price = content.get(color + "_" + sku + "_pricestd", "")
                    agentprice = content.get(color + "_" + sku + "_agentprice", "")
                    one_sku = ProductSku(outer_id=outer_id, product=one_product, remain_num=remain_num,
                                         cost=cost, std_sale_price=price, agent_price=agentprice,
                                         properties_name=sku, properties_alias=sku, barcode=barcode)
                    one_sku.save()
                    log_action(user.id, one_sku, ADDITION, u'新建一个sku_new')
                    count += 1
            except Exception,exc:
                logger.error(exc.message or u'商品资料创建错误',exc_info=True)
                raise exceptions.APIException(u'出错了:%s'% exc.message)
        # 发送　添加供应商总选款的字段　的信号
        try:
            signal_record_supplier_models.send(sender=ModelProduct, obj=model_pro)
        except Exception, exc:
            logger.error(exc.message or u'创建商品model异常', exc_info=True)
            raise exceptions.APIException(u'创建商品model异常:%s' % exc.message)

        logger.info('modelproduct-create: inner_outer_id= %s, model_id= %s' % (inner_outer_id, model_pro.id))
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
                third_child_category = self.queryset.filter(
                    parent_cid=c_category.cid)
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
        ware_by = 0
        if all_supplier:
            ware_by = all_supplier[0].ware_by
        return Response({'all_supplier': {"0": result_data}, 'ware_by': ware_by})


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
        try:
            if product_bean.count() > 0:
                all_sku = product_bean[0].normal_skus.values_list('properties_alias', flat=True)
                result_data = {}
                constants_map = ContrastContent.contrast_maps()
                for one_sku in all_sku:
                    contrast_tables = product_bean[0].contrast.contrast_detail.get(one_sku)
                    for one_chima, chima_size in contrast_tables.iteritems():
                        try:
                            one_chima_name = constants_map.get(one_chima) or one_chima
                        except:
                            continue
                        if one_sku in result_data:
                            result_data[one_sku].append((one_chima, one_chima_name, chima_size))
                        else:
                            result_data[one_sku] = [(one_chima, one_chima_name, chima_size)]

                # chima_content = product_bean[0].contrast.get_correspond_content
                chima_content = result_data.items()
                chima_content.sort(cmp=custom_sort)
                return Response({"result": chima_content,
                                 "product_id": product_bean[0].id,
                                 "searchtext": searchtext})
            else:
                return Response({"result": "NOTFOUND",
                                 "searchtext": searchtext})
        except:
            return Response({"result": "NOTFOUND",
                             "product_id": product_bean[0].id,
                             "searchtext": searchtext})

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
                all_chi_ma.add(k.split("_")[2].strip())
        chi_ma_result = {}
        for sku in all_sku:
            for chi_ma in all_chi_ma:
                chi_ma_content = content.get(str(product_model.id) + "_" + sku + "_" + chi_ma)
                if chi_ma_content and len( chi_ma_content) > 0 and chi_ma_content != "0":
                    if sku in chi_ma_result:
                        chi_ma_result[sku][chi_ma] = chi_ma_content
                    else:
                        chi_ma_result[sku] = {chi_ma: chi_ma_content}
        try:
            product_model.contrast.contrast_detail = chi_ma_result
            product_model.contrast.save()
            log_action(user.id, product_model, CHANGE, u'修改尺码表内容')
        except:
            chima_model = ProductSkuContrast(product=product_model,
                                             contrast_detail=chi_ma_result)
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
        product_bean = Product.objects.filter(Q(outer_id=searchtext) | Q(
            id=searchtext)).filter(status=Product.NORMAL)
        if product_bean.count() > 0:
            chima_content = product_bean[0].contrast.get_correspond_content
            chima_content = chima_content.items()
            chima_content.sort(cmp=custom_sort)
            return Response({"result": chima_content,
                             "product_id": product_bean[0].id,
                             "searchtext": searchtext})
        else:
            return Response({"result": "NOTFOUND",
                             "searchtext": searchtext})


def custom_sort(a, b):
    if a[0].isdigit() and b[0].isdigit():
        return int(a[0]) - int(b[0])

    if a[0].isdigit() and not b[0].isdigit():
        return True

    if not a[0].isdigit() and b[0].isdigit():
        return False

    return len(a[0]) - len(b[0]) or a[0] > b[0]


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
        parent_categorys = ProductCategory.objects.filter(
            is_parent=True).exclude(name__in=ex_names)
        p_cates = []
        for parent in parent_categorys:
            p_kv = {"p_cid": parent.cid,
                    "p_fullcate_name": parent.__unicode__()}
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
            products = Product.objects.filter(
                model_id__in=models,
                status=Product.NORMAL).order_by("outer_id")
        elif p_cate_search is not None and p_cate_search != "":
            products = Product.objects.filter(
                sale_time=target_shelf_date,
                status=Product.NORMAL,
                category__parent_cid=p_cate_search).order_by("outer_id")
        else:
            products = []
        rebeta_schemes = AgencyOrderRebetaScheme.objects.filter(
            status=AgencyOrderRebetaScheme.NORMAL)
        print 'debug:', rebeta_schemes
        return Response({"all_product": products,
                         "model_id": model_id,
                         "target_shelf_date": target_shelf_date,
                         "cates": cates,
                         "ware_by": WARE_CHOICES,
                         "rebeta_schemes": rebeta_schemes,
                         "p_cates": p_cates})

    def add_kill_title(self, pros, actioner):
        """ 添加秒杀标题  添加款式的苗烧标题 """
        for pro in pros:
            title = pro.title()
            if not title.startswith('秒杀'):  # 防止重复添加秒杀
                pro.name = '秒杀 ' + title
                # 添加备注　秒杀不退不换
                pro.memo += u'秒杀商品，一经售出，概不退换'
                pro.save()
                log_action(actioner, pro, CHANGE, u'批量添加秒杀标题')
            model_id = pro.model_id
        try:
            model = ModelProduct.objects.get(id=model_id)
            model_name = model.name
            if not model_name.startswith('秒杀'):
                model.name = '秒杀 ' + model_name
                model.save()
                log_action(actioner, model, CHANGE, u'批量添加秒杀标题')
        except:
            pass
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
            model_id = pro.model_id
        try:
            model = ModelProduct.objects.get(id=model_id)
            model_name = model.name
            if model_name.startswith('秒杀'):
                model.name = model_name.replace("秒杀", "").lstrip()
                model.save()
                log_action(actioner, model, CHANGE, u'批量删除秒杀标题')
        except:
            pass
        return

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        content = request.POST
        target_product = content.get("product_list", None)
        add_kill_title = content.get("add_kill_title", None)
        all_product = target_product.split(",")
        pros = Product.objects.filter(id__in=all_product)
        if add_kill_title and int(add_kill_title) == 1:  # 添加秒杀标题
            self.add_kill_title(pros, request.user.id)
        elif add_kill_title and int(add_kill_title) == 0:  # 移除秒杀
            self.remove_kill_title(pros, request.user.id)
        for pro in pros:
            properties = []
            product_detail, state = Productdetail.objects.get_or_create(
                product=pro)
            update_detail = False
            for k, v in request.data.iteritems():
                k = str(k)
                if k in ("offshelf_time", "sale_time", "ware_by",
                         "agent_price") and v == "":
                    continue
                if hasattr(pro, k):
                    if k == 'is_watermark' and v:
                        setattr(pro, k, int(v))
                    if k == 'is_sale' and v:
                        setattr(pro, k, int(v))
                    properties.append((Product._meta.get_field(
                        k).verbose_name.title(), v))

                if k == 'agent_price':
                    pro.pskus.update(agent_price=v)

                if k == 'rebeta_scheme_id' and v != '':
                    product_detail.rebeta_scheme_id = v
                    update_detail = True
                if k == 'is_sale' and v != '':
                    product_detail.is_sale = int(v)
                    update_detail = True
            pro.save()

            if update_detail:
                product_detail.save()
                properties.append((Productdetail._meta.get_field(
                    k).verbose_name.title(), v))

            if k:
                log_action(request.user.id, pro, CHANGE,
                           u'批量设置产品:%s' % (','.join('%s＝%s' % p
                                                    for p in properties)))
        return Response({"code": 0})


class ProductScheduleView(generics.ListCreateAPIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = 'items/product_schedule.html'

    warehouses = [{'id': WARE_NONE, 'name': u'未选仓'}, {'id': WARE_SH, 'name': u'上海仓'},
                  {'id': WARE_GZ, 'name': u'广州仓'}]
    warehouse_mapping = {row['id']: row['name'] for row in warehouses}
    sale_types = [{'id': row[0], 'name': row[1]} for row in constants.SALE_TYPES]
    sale_type_mapping = {row[0]: row[1] for row in constants.SALE_TYPES}

    @property
    def categories(self):
        return local_cache.product_category_cache.categories

    @property
    def schemas(self):
        return local_cache.rebeta_schema_cache.schemas

    @property
    def category_mapping(self):
        return {row['id']: row['name'] for row in self.schemas}

    @classmethod
    def product_to_item(cls, row):
        row.pic = row.thumbnail
        row.schedule_id = 0
        row.product_id = row.id
        row.category_name = cls.category_mapping.get(row.category_id) or ''
        row.warehouse_name = cls.warehouse_mapping.get(int(row.ware_by)) or ''
        return row

    @classmethod
    def schedule_to_item(cls, row):
        row.pic = row.product.thumbnail
        row.schedule_id = row.id
        row.id = row.product.id
        row.category_name = cls.category_mapping.get(
            row.product.category_id) or ''
        row.warehouse_name = cls.warehouse_mapping.get(int(
            row.product.ware_by)) or ''
        row.cost = row.product.cost
        row.agent_price = row.product.agent_price
        row.name = row.product.name
        row.outer_id = row.product.outer_id
        row.model_id = row.product.model_id
        row.product_id = 0
        row.is_watermark = row.product.is_watermark
        row.sale_name = cls.sale_type_mapping.get(row.sale_type) or ''
        return row

    def get(self, request, p=1, **kwargs):
        p = int(p)
        now = datetime.datetime.now()
        today = now.date()

        date_shortcuts = []
        for i in range(-6, 8):
            d = today + datetime.timedelta(days=i)
            date_shortcuts.append({
                'value': d.strftime('%Y-%m-%d'),
                'name': d.strftime('%m月%d日')
            })
        data = {
            'color': '#ff69b4',
            'warehouses': self.warehouses,
            'categories': self.categories,
            'schemas': self.schemas,
            'date_shortcuts': date_shortcuts,
            'sale_types': self.sale_types
        }
        form = forms.ProductScheduleForm(request.GET)
        if not form.is_valid() or form.is_empty():
            return Response(data)

        items = []
        pagination_row = ''
        params = {k: v for k, v in form.cleaned_data.iteritems() if v != None}

        if not form.has_schedule_params():
            query = form.get_product_query()
            count = Product.objects.filter(**query).count()
            paginator = Paginator(range(count), constants.PAGE_SIZE)
            if paginator.num_pages < p:
                p = 1
            if count:
                pagination_row = page_helper.get_pagination_row(
                    paginator,
                    p,
                    'product_schedule',
                    {},
                    page_threshold=5,
                    params=params)
                page = paginator.page(p)
                rows = Product.objects.select_related('category').filter(
                    **query).order_by('-id')[
                       page.object_list[0]:page.object_list[-1] + 1]

                for row in rows:
                    row = self.product_to_item(row)
                items = rows
        else:
            query = form.get_schedule_query()
            count = ProductSchedule.objects.filter(**query).count()
            paginator = Paginator(range(count), constants.PAGE_SIZE)
            if paginator.num_pages < p:
                p = 1
            if count:
                pagination_row = page_helper.get_pagination_row(
                    paginator,
                    p,
                    'product_schedule',
                    {},
                    page_threshold=5,
                    params=params)
                page = paginator.page(p)
                rows = ProductSchedule.objects.select_related(depth=1).filter(
                    **query).order_by('-product__id', '-id')[page.object_list[0]:
                       page.object_list[-1] + 1]
                for row in rows:
                    row = self.schedule_to_item(row)
                items = rows
        data.update({
            'items': items,
            'pagination_row': pagination_row,
            'form': form.json
        })
        return Response(data)

    def post(self, request, p=1, **kwargs):
        p = int(p)
        now = datetime.datetime.now()
        today = now.date()

        date_shortcuts = []
        for i in range(-6, 8):
            d = today + datetime.timedelta(days=i)
            date_shortcuts.append({
                'value': d.strftime('%Y-%m-%d'),
                'name': d.strftime('%m月%d日')
            })
        data = {
            'color': '#ff69b4',
            'warehouses': self.warehouses,
            'categories': self.categories,
            'schemas': self.schemas,
            'date_shortcuts': date_shortcuts,
            'sale_types': self.sale_types
        }
        form = forms.ProductScheduleForm(request.POST)
        if not form.is_valid() or form.is_empty():
            return Response(data)

        items = []
        reload_url = ''
        pagination_row = ''
        product_ids = json.loads(form.cleaned_attrs.product_ids)
        schedule_ids = json.loads(form.cleaned_attrs.schedule_ids)

        if not (product_ids or schedule_ids):
            return Response(data)

        if product_ids:
            product_ids = map(int, product_ids)
            reload_url = '%s?%s' % (
            reverse('product_schedule'), urllib.urlencode({'product_ids': json.dumps(product_ids)}))
            Product.objects.filter(id__in=product_ids).update(
                **form.get_product_update_kwargs())
            rows = Product.objects.filter(id__in=product_ids).order_by('-id')
            for row in rows:
                is_dirty = False
                # 处理秒杀
                if form.cleaned_attrs.is_seckill:
                    if not row.name.startswith('秒杀'):
                        row.name = '秒杀 ' + row.name
                        row.memo += u'秒杀商品，一经售出，概不退换'
                        is_dirty = True
                if form.cleaned_attrs.is_not_seckill:
                    if row.name.startswith('秒杀'):
                        row.name = row.name.replace('秒杀', '').lstrip()
                        row.memo = row.memo.replace(u'秒杀商品，一经售出，概不退换', u'')
                        is_dirty = True

                if form.cleaned_attrs.price:
                    row.agent_price = form.cleaned_attrs.price
                    row.pskus.update(agent_price=form.cleaned_attrs.price)
                    is_dirty = True

                if form.cleaned_attrs.rebeta_schema_id:
                    product_detail, _ = Productdetail.objects.get_or_create(
                        product=row)
                    product_detail.rebeta_scheme_id = form.cleaned_attrs.rebeta_schema_id
                    product_detail.save()
                if is_dirty:
                    row.save()

                if form.cleaned_attrs.onshelf_datetime_start and \
                        form.cleaned_attrs.offshelf_datetime_start:

                    # 　生成排期数据
                    # 查询是否存在重叠的排期数据
                    status = 0 if ProductSchedule.objects.filter(
                        onshelf_datetime__lte=
                        form.cleaned_attrs.offshelf_datetime_start,
                        offshelf_datetime__gte=
                        form.cleaned_attrs.onshelf_datetime_start) else 1
                    schedule = ProductSchedule(
                        product=row,
                        onshelf_datetime=
                        form.cleaned_attrs.onshelf_datetime_start,
                        onshelf_date=
                        form.cleaned_attrs.onshelf_datetime_start.date(),
                        onshelf_hour=int(
                            form.cleaned_attrs.onshelf_datetime_start.strftime(
                                '%H')),
                        offshelf_datetime=
                        form.cleaned_attrs.offshelf_datetime_start,
                        offshelf_date=
                        form.cleaned_attrs.offshelf_datetime_start.date(),
                        offshelf_hour=int(
                            form.cleaned_attrs.offshelf_datetime_start.strftime(
                                '%H')),
                        status=status)
                    schedule.save()
                    items.append(self.schedule_to_item(schedule))
                else:
                    items.append(self.product_to_item(row))

        else:
            schedule_ids = map(int, schedule_ids)
            reload_url = '%s?%s' % (
            reverse('product_schedule'), urllib.urlencode({'schedule_ids': json.dumps(schedule_ids)}))
            schedule_update_kwargs = form.get_schedule_update_kwargs()

            if schedule_update_kwargs:
                ProductSchedule.objects.filter(pk__in=schedule_ids).update(
                    **schedule_update_kwargs)
            rows = ProductSchedule.objects.select_related(depth=1).filter(
                pk__in=schedule_ids)
            product_ids = [row.product.id for row in rows]
            product_update_kwargs = form.get_product_update_kwargs()
            if product_update_kwargs:
                Product.objects.filter(pk__in=product_ids).update(
                    **product_update_kwargs)

            if form.cleaned_attrs.is_seckill or form.cleaned_attrs.is_not_seckill or form.cleaned_attrs.price or \
                    form.cleaned_attrs.rebeta_schema_id:
                for row in Product.objects.filter(pk__in=product_ids):
                    is_dirty = False
                    if form.cleaned_attrs.is_seckill:
                        if not row.name.startswith('秒杀'):
                            row.name = '秒杀' + row.name
                            row.memo += u'秒杀商品，一经售出，概不退换'
                            is_dirty = True
                    if form.cleaned_attrs.is_not_seckill:
                        if row.name.startswith('秒杀'):
                            row.name = row.name.replace('秒杀', '').lstrip()
                            row.memo = row.memo.replace(u'秒杀商品，一经售出，概不退换', u'')
                            is_dirty = True
                    if form.cleaned_attrs.price:
                        row.agent_price = form.cleaned_attrs.price
                        row.pskus.update(agent_price=form.cleaned_attrs.price)
                        is_dirty = True

                    if form.cleaned_attrs.rebeta_schema_id:
                        product_detail, _ = Productdetail.objects.get_or_create(
                            product=row)
                        product_detail.rebeta_scheme_id = form.cleaned_attrs.rebeta_schema_id
                        product_detail.save()
                    if is_dirty:
                        row.save()

            # 重新取数据
            rows = ProductSchedule.objects.select_related(depth=1).filter(
                pk__in=schedule_ids).order_by('-product__id', '-id')
            for row in rows:
                row = self.schedule_to_item(row)
            items = rows

        data.update({
            'items': items,
            'pagination_row': pagination_row,
            'form': form.json,
            'reload_url': mark_safe(reload_url)
        })
        return Response(data)


class ProductScheduleAPIView(generics.ListCreateAPIView):
    def post(self, request, **kwargs):
        form = forms.ProductScheduleAPIForm(request.POST)
        if not form.is_valid():
            return Response({'success': False})

        if form.cleaned_attrs.schedule_id:
            rows = ProductSchedule.objects.filter(pk=form.cleaned_attrs.schedule_id)
            if rows:
                product_id = rows[0].product_id
            else:
                return Response({'success': False})
        else:
            product_id = form.cleaned_attrs.product_id

        if form.cleaned_attrs.type == constants.SCHEDULE_API_TYPE_PRICE:
            Product.objects.filter(pk=product_id).update(agent_price=form.cleaned_attrs.price)
            for row in Product.objects.filter(pk=product_id):
                row.pskus.update(agent_price=form.cleaned_attrs.price)

        if form.cleaned_attrs.type == constants.SCHEDULE_API_TYPE_SECKILL:
            rows = Product.objects.filter(pk=product_id)
            if not rows:
                return Response({'success': False})
            row = rows[0]
            if form.cleaned_attrs.flag:
                # row.is_seckill = True
                if not row.name.startswith('秒杀'):
                    row.name = '秒杀' + row.name
                    row.memo += u'秒杀商品，一经售出，概不退换'
            else:
                # row.is_seckill = False
                if row.name.startswith('秒杀'):
                    row.name = row.name.replace('秒杀', '').lstrip()
                    row.memo = row.memo.replace(u'秒杀商品，一经售出，概不退换', u'')
            row.save()

        if form.cleaned_attrs.type == constants.SCHEDULE_API_TYPE_WATERMARK:
            if form.cleaned_attrs.flag:
                Product.objects.filter(pk=product_id).update(is_watermark=True)
            else:
                Product.objects.filter(pk=product_id).update(is_watermark=False)

        if form.cleaned_attrs.type == constants.SCHEDULE_API_TYPE_STATUS:
            schedule_id = form.cleaned_attrs.schedule_id
            if schedule_id:
                status = form.cleaned_attrs.flag and 1 or 0
                ProductSchedule.objects.filter(pk=schedule_id).update(status=status)
        return Response({'success': False})
