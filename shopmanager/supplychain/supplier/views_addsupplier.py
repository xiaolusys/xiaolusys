# coding: utf-8
import datetime
import json
import urllib

from rest_framework import generics
from shopback.categorys.models import ProductCategory

from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response

from django.contrib import messages
from django.db import transaction
from django.db.models import F, Q

from flashsale.pay.models_custom import Productdetail
from shopback.base import log_action, ADDITION, CHANGE
from shopback import paramconfig as pcfg
from supplychain.supplier.models import SaleSupplier, SaleCategory, SaleProductManage, SaleProductManageDetail, \
    SupplierZone, SaleProductPicRatingMemo
from supplychain.supplier.models import SaleProduct

from . import forms


class AddSupplierView(generics.ListCreateAPIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "add_supplier.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        platform_choice = SaleSupplier.PLATFORM_CHOICE
        process_choice = SaleSupplier.PROGRESS_CHOICES
        all_category = SaleCategory.objects.filter()
        zones = SupplierZone.objects.all()
        return Response({"platform_choice": platform_choice,
                         "all_category": all_category,
                         "process_choice": process_choice,
                         "supplier_types": SaleSupplier.SUPPLIER_TYPE,
                         "zones": zones})

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
        speciality = post.get("speciality", '')
        supplier_type = post.get("supplier_type", 0)
        supplier_zone = post.get("supplier_zone", 0)

        new_supplier = SaleSupplier(supplier_name=supplier_name,
                                    supplier_code=supplier_code,
                                    main_page=main_page,
                                    platform=platform,
                                    category_id=category,
                                    contact=contact_name,
                                    mobile=mobile,
                                    address=address,
                                    memo=memo,
                                    progress=progress,
                                    speciality=speciality,
                                    supplier_type=supplier_type,
                                    supplier_zone=supplier_zone)
        new_supplier.save()
        log_action(request.user.id, new_supplier, ADDITION, u'新建'.format(""))
        return Response({"supplier_id": new_supplier.id})


class CheckSupplierView(generics.ListCreateAPIView):
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        post = request.POST
        supplier_name = post.get("supplier_name", "")
        suppliers = SaleSupplier.objects.filter(
            supplier_name__contains=supplier_name)
        if suppliers.count() > 10:
            return Response({"result": "more"})
        if suppliers.count() > 0:
            return Response({"result": "10",
                             "supplier": [s.supplier_name for s in suppliers]})
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
        goodshelf = GoodShelf.objects.get(
            active_time__range=(target_date, end_time))
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
        from shopback.items.local_cache import rebeta_schema_cache

        target_date_str = request.GET.get(
            "target_date", datetime.date.today().strftime("%Y-%m-%d"))
        category = request.GET.get("category", "0")
        result_data = []
        target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d')
        for i in range(0, 6):
            temp_date = target_date + datetime.timedelta(days=i)
            one_data, wem_posters, chd_posters, target_sch = get_target_date_detail(
                temp_date, category)
            result_data.append({"data": one_data,
                                "date": temp_date.strftime("%Y-%m-%d"),
                                "wem_posters": wem_posters,
                                "chd_posters": chd_posters})

        return Response(
            {"result_data": result_data,
             "target_date": target_date_str,
             "category": category,
             'show_pic_rating_btn': request.user.has_perm(
                 'supplier.pic_rating'),
             'schemas': rebeta_schema_cache.schemas,
             'order_weights': [{'id': i,
                                'name': i} for i in range(1, 17)[::-1]],
             'show_buyer_btn': request.user.has_perm('supplier.add_product'),
             'show_eliminate_btn': request.user.has_perm(
                 'supplier.eliminate_product')})


class ScheduleCompareView(generics.ListCreateAPIView):
    """排期比较"""
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    permission_classes = (permissions.IsAuthenticated,)
    template_name = "schedulecompare.html"

    def get(self, request, *args, **kwargs):
        target_date_str = request.GET.get(
            "target_date", datetime.date.today().strftime("%Y-%m-%d"))
        target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d')
        try:
            end_time = target_date + datetime.timedelta(days=1)
        except:
            return "", "", ""
        lock_schedule = SaleProductManage.objects.filter(sale_time=target_date)
        if lock_schedule.count() == 0:
            return Response({"result": "0", "target_date": target_date_str})
        now_sachedule = SaleProduct.objects.filter(sale_time__gte=target_date,
                                                   sale_time__lt=end_time,
                                                   status=SaleProduct.SCHEDULE)
        lock_list = set([one_product.sale_product_id
                         for one_product in lock_schedule[0].normal_detail])
        now_list = set([one_product.id for one_product in now_sachedule])
        result_list = (lock_list | now_list) - (lock_list & now_list)
        return Response({"result_data": result_list,
                         "target_date": target_date_str})


class SaleProductAPIView(generics.ListCreateAPIView):
    """
        *   get:获取每个选品的资料（库存、model、detail）
        *   post:
                -   type:1 设计接管选品
                -   type:2 排期完成，即设计组完成图片
                -   type:3 取消排期完成
                -   type:4 作图评分
    """
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        from shopback.items.local_cache import rebeta_schema_cache

        sale_product_id = request.GET.get("sale_product")
        if not sale_product_id:
            return Response({"flag": "error"})
        sale_product = SaleProduct.objects.get(pk=sale_product_id)
        librarian = sale_product.librarian or ''
        supplier_id = sale_product.sale_supplier_id
        add_product_url = '%s?%s' % (
            '/static/add_item.html',
            urllib.urlencode({'supplier_id': supplier_id,
                              'saleproduct': sale_product_id}))

        all_product = Product.objects.filter(status=Product.NORMAL,
                                             sale_product=sale_product_id)
        if all_product.count() == 0:
            return Response({
                'flag': 'working',
                'librarian': librarian,
                'username': request.user.username,
                'add_product_url': add_product_url,
                'show_buyer_btn': request.user.has_perm('supplier.add_product')
            })
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
        std_purchase_price = all_product[0].std_purchase_price
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

        # productdetail
        schema_mapping = {i['id']: i['name']
                          for i in rebeta_schema_cache.schemas}
        watermark_set = set()
        seckill_set = set()
        recommend_set = set()
        order_weights = []
        total_price = []
        schema_set = set()
        for p in all_product:
            watermark_set.add(p.is_watermark)
            if p.agent_price:
                total_price.append(p.agent_price)
            if hasattr(p, 'details'):
                seckill_set.add(p.details.is_seckill)
                recommend_set.add(p.details.is_recommend)
                order_weights.append(p.details.order_weight or 0)
                schema = schema_mapping.get(p.details.rebeta_scheme_id) or ''
                if schema:
                    schema_set.add(schema)

        sale_product_is_watermark = ''
        sale_product_is_seckill = ''
        sale_product_is_recommend = ''
        sale_product_order_weight = ''
        sale_product_price = ''
        sale_product_rebeta_schema = ''
        if len(watermark_set) > 1:
            sale_product_is_watermark = '水印：不一致'
        elif len(watermark_set) == 1:
            sale_product_is_watermark = '水印：%s' % ('是' if watermark_set.pop()
                                                   else '否',)
        if len(seckill_set) > 1:
            sale_product_is_seckill = '秒杀：不一致'
        elif len(seckill_set) == 1:
            sale_product_is_seckill = '秒杀：%s' % ('是' if seckill_set.pop() else
                                                 '否',)
        if len(recommend_set) > 1:
            sale_product_is_recommend = '专区推荐：不一致'
        elif len(recommend_set) == 1:
            sale_product_is_recommend = '专区推荐：%s' % ('是' if recommend_set.pop()
                                                     else '否',)
        if len(schema_set) > 1:
            sale_product_rebeta_schema = '返利计划：不一致'
        elif len(schema_set) == 1:
            sale_product_rebeta_schema = '返利计划：%s' % schema_set.pop()

        order_weights = filter(None, order_weights)
        if order_weights:
            avg_order_weight = round(sum(order_weights) / len(order_weights), 2)
        if avg_order_weight:
            sale_product_order_weight = '权值：%.2f' % avg_order_weight
        total_price = filter(None, total_price)
        if total_price:
            sale_product_price = '出售平均价：%.2f' % (sum(total_price) /
                                                 len(total_price),)
        return Response(
            {"flag": "done",
             "color_list": color_list,
             "sku_list": sku_list,
             "name": name,
             "zhutu": zhutu,
             "lowest_price": lowest_price,
             "std_sale_price": std_sale_price,
             "sale_charger": sale_charger,
             "std_purchase_price": std_purchase_price,
             "model_id": model_id,
             "single_model": single_model,
             "product_id": product_id,
             'sale_product_is_watermark': sale_product_is_watermark,
             'sale_product_is_seckill': sale_product_is_seckill,
             'sale_product_is_recommend': sale_product_is_recommend,
             'sale_product_order_weight': sale_product_order_weight,
             'sale_product_price': sale_product_price,
             'sale_product_rebeta_schema': sale_product_rebeta_schema,
             'librarian': librarian,
             'show_buyer_btn': request.user.has_perm('supplier.add_product'),
             'add_product_url': add_product_url,
             'username': request.user.username})

    def post(self, request, *args, **kwargs):
        detail = request.POST.get("detail_id")
        type = request.POST.get("type")
        sale_product_id = request.POST.get('sale_product')
        if type == '5':
            SaleProduct.objects.filter(pk=int(sale_product_id),
                                       librarian__isnull=True).update(
                                           librarian=request.user.username)
            return Response({'result': u'ok'})

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
            return Response({"result": u"success",
                             "username": request.user.username})
        elif type == "2":
            if detail_product.design_complete:
                return Response({"result": u"alreadycomplete"})
            if detail_product.design_person != request.user.username:
                return Response({"result": u"not_same_people"})
            detail_product.design_complete = True
            detail_product.save()
            log_action(request.user.id, detail_product, CHANGE, u'完成')
            return Response({"result": u"success"})
        elif type == "3":
            if not detail_product.design_complete:
                return Response({"result": u"notdone"})
            if detail_product.design_person != request.user.username and not request.user.has_perm(
                    'supplier.revert_done'):
                return Response({"result": u"forbidden"})
            detail_product.design_complete = False
            detail_product.save()
            log_action(request.user.id, detail_product, CHANGE, u'反完成')
            return Response({"result": u"success"})
        elif type == '4':
            """
            if not detail_product.design_complete:
                return Response({'result': u'notdone'})
            """
            if not request.user.has_perm('supplier.pic_rating'):
                return Response({'result': u'forbidden'})
            memo = request.POST.get('memo') or ''
            rating = float(request.POST.get('rating') or 0)

            pic_rating_memo = None
            if memo:
                pic_rating_memo = SaleProductPicRatingMemo(
                    memo=memo,
                    user=request.user,
                    schedule_detail=detail_product)
                pic_rating_memo.save()

            detail_product.pic_rating = rating
            detail_product.save()
            result = {} if not pic_rating_memo else {'memo':
                                                     unicode(pic_rating_memo)}
            return Response(result)
        elif type == '6':
            sale_product_id = detail_product.sale_product_id
            mlist = []
            for p in Product.objects.filter(
                    Q(sale_product=sale_product_id),
                    Q(collect_num__gt=0) | Q(wait_post_num__gt=0)
                    | Q(shelf_status=Product.UP_SHELF)):
                s = '商品编码：%s 不能作废原因：' % p.outer_id
                mitems = []
                if p.collect_num > 0:
                    mitems.append('库存不为0')
                if p.wait_post_num > 0:
                    mitems.append('待发数不为0')
                if p.shelf_status == Product.UP_SHELF:
                    mitems.append('商品未下架')
                message = '%s%s' % (s, ','.join(mitems))
                mlist.append(message)
                messages.add_message(request, messages.INFO, message)
            if mlist:
                return Response({'result': 'fail'})
            # 先作废库存商品
            for p in Product.objects.filter(sale_product=sale_product_id, status__in=[pcfg.NORMAL, pcfg.REMAIN]):
                cnt = 0
                success = False
                invalid_outerid = p.outer_id
                while cnt < 10:
                    invalid_outerid += '_del'
                    if Product.objects.filter(outer_id=invalid_outerid).count() == 0:
                        success = True
                        break
                    cnt += 1
                if not success:
                    continue
                p.outer_id = invalid_outerid
                p.status = Product.DELETE
                p.save()
            # 作废SaleProduct
            SaleProduct.objects.filter(pk=sale_product_id).update(status=SaleProduct.REJECTED)

            # 删除排期记录
            SaleProductManageDetail.objects.filter(id=detail).delete()
            return Response({'result': 'success'})

        return Response({"result": u"error"})


class ScheduleBatchSetView(generics.ListCreateAPIView):
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        form = forms.ScheduleBatchSetForm(request.POST)
        if not form.is_valid():
            return Response('fail')

        detail_ids = map(int, json.loads(form.cleaned_attrs.detail_ids))
        sale_product_ids = []
        for row in SaleProductManageDetail.objects.filter(pk__in=detail_ids):
            sale_product_ids.append(row.sale_product_id)
        sale_product_ids = list(set(sale_product_ids))

        if form.cleaned_attrs.onshelf_date:
            mgr_p, state = SaleProductManage.objects.get_or_create(sale_time=form.cleaned_attrs.onshelf_date)
            if not state and mgr_p.lock_status:
                messages.add_message(request, messages.INFO, '%s排期已经被锁定' % form.cleaned_attrs.onshelf_date.strftime('%Y%m%d'))
            else:
                SaleProductManageDetail.objects.filter(pk__in=detail_ids).update(today_use_status=SaleProductManageDetail.DELETE)
                for row in SaleProduct.objects.filter(pk__in=sale_product_ids):
                    #　生成one_detail
                    one_detail, _ = SaleProductManageDetail.objects.get_or_create(schedule_manage=mgr_p, sale_product_id=row.id)
                    one_detail.name = row.title
                    one_detail.today_use_status = SaleProductManageDetail.NORMAL
                    one_detail.pic_path = row.pic_url
                    one_detail.product_link = row.product_link
                    try:
                        category = row.sale_category.full_name
                    except:
                        category = ''
                    one_detail.sale_category = category
                    one_detail.save()
                    # 设置saleproduct的sale_time
                    row.sale_time = datetime.datetime.combine(form.cleaned_attrs.onshelf_date,
                                                                  datetime.datetime.min.time())
                    row.save()
                    # 设置product上架时间
                    Product.objects.filter(sale_product=row.id, status=Product.NORMAL).update(sale_time=form.cleaned_attrs.onshelf_date)
                # 统计mgr_p的数量
                mgr_p.product_num = mgr_p.manage_schedule.filter(today_use_status=SaleProductManageDetail.NORMAL).count()
                # 更新负责人名称
                if not mgr_p.responsible_people_id:
                    mgr_p.responsible_people_id = request.user.id
                    mgr_p.responsible_person_name = request.user.username
                mgr_p.save()


        for row in Product.objects.filter(sale_product__in=sale_product_ids):
            is_dirty = False
            if form.cleaned_attrs.price:
                is_dirty = True
                row.agent_price = form.cleaned_attrs.price
            if form.cleaned_attrs.is_watermark:
                is_dirty = True
                row.is_watermark = True
            if form.cleaned_attrs.cancel_watermark:
                is_dirty = True
                row.is_watermark = False

            if form.cleaned_attrs.sync_stock:
                is_dirty = True
                row.remain_num = row.collect_num
            if is_dirty:
                row.save()

            is_dirty = False
            product_detail, _ = Productdetail.objects.get_or_create(product=row)
            if form.cleaned_attrs.is_recommend:
                is_dirty = True
                product_detail.is_recommend = True
            if form.cleaned_attrs.cancel_recommend:
                is_dirty = True
                product_detail.is_recommend = False

            if form.cleaned_attrs.rebeta_schema_id:
                is_dirty = True
                product_detail.rebeta_scheme_id = form.cleaned_attrs.rebeta_schema_id
            if form.cleaned_attrs.order_weight:
                is_dirty = True
                product_detail.order_weight = form.cleaned_attrs.order_weight
            if form.cleaned_attrs.is_seckill:
                is_dirty = True
                product_detail.is_seckill = True
                if not row.name.startswith('秒杀'):
                    row.name = '秒杀 ' + row.name
                row.memo = row.memo.replace(u'秒杀商品，一经售出，概不退换', u'')
                row.memo += u'秒杀商品，一经售出，概不退换'
                row.save()
            if form.cleaned_attrs.cancel_seckill:
                is_dirty = True
                product_detail.is_seckill = False
                if row.name.startswith('秒杀'):
                    row.name = row.name.replace('秒杀', '').lstrip()
                row.memo = row.memo.replace(u'秒杀商品，一经售出，概不退换', u'')
                row.save()

            if is_dirty:
                product_detail.save()
        return Response('ok')
