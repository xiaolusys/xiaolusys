# coding: utf-8
__author__ = 'yann'

import datetime
from .. import functions
import json

from django.contrib.auth.models import User
from django.db import connection
from django.db.models import Max, Sum, Q
from django.forms.models import model_to_dict
from django.shortcuts import render, HttpResponse
from django.template import RequestContext
from django.views.generic import View

from rest_framework import permissions, viewsets
from rest_framework.decorators import list_route
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response

from flashsale.dinghuo.models import OrderDetail, OrderList
from flashsale.dinghuo.tasks import task_ding_huo_optimize, task_ding_huo
from shopback import paramconfig as pcfg
from shopback.items.models import Product, ProductSku
from shopback.trades.models import (MergeOrder, TRADE_TYPE, SYS_TRADE_STATUS)
from supplychain.supplier.models import SaleProduct, SaleProductManage, SaleProductManageDetail

from . import forms


class DailyDingHuoView(View):
    def parseEndDt(self, end_dt):
        if not end_dt:
            dt = datetime.datetime.now()
            return datetime.datetime(dt.year, dt.month, dt.day, 23, 59, 59)
        if len(end_dt) > 10:
            return functions.parse_datetime(end_dt)
        return functions.parse_date(end_dt)

    def get(self, request):
        content = request.GET
        today = datetime.date.today()
        shelve_fromstr = content.get("df", None)
        shelve_to_str = content.get("dt", None)
        query_time_str = content.get("showt", None)
        groupname = content.get("groupname", 0)
        dhstatus = content.get("dhstatus", '1')
        groupname = int(groupname)
        search_text = content.get("search_text", '').strip()
        target_date = today
        if shelve_fromstr:
            year, month, day = shelve_fromstr.split('-')
            target_date = datetime.date(int(year), int(month), int(day))
            if target_date > today:
                target_date = today

        shelve_from = datetime.datetime(target_date.year, target_date.month,
                                        target_date.day)
        time_to = self.parseEndDt(shelve_to_str)
        if time_to - shelve_from < datetime.timedelta(0):
            time_to = shelve_from + datetime.timedelta(1)
        query_time = self.parseEndDt(query_time_str)
        order_sql = "select id,outer_id,sum(num) as sale_num,outer_sku_id,pay_time from " \
                    "shop_trades_mergeorder where sys_status='IN_EFFECT' " \
                    "and merge_trade_id in (select id from shop_trades_mergetrade where type not in ('reissue','exchange') " \
                    "and status in ('WAIT_SELLER_SEND_GOODS','WAIT_BUYER_CONFIRM_GOODS','TRADE_BUYER_SIGNED','TRADE_FINISHED') " \
                    "and sys_status not in('INVALID','ON_THE_FLY') " \
                    "and id not in (select id from shop_trades_mergetrade where sys_status='FINISHED' and is_express_print=False))" \
                    "and gift_type !=4 " \
                    "and (pay_time between '{0}' and '{1}') " \
                    "and char_length(outer_id)>=9 " \
                    "and (left(outer_id,1)='9' or left(outer_id,1)='8' or left(outer_id,1)='1') " \
                    "group by outer_id,outer_sku_id".format(shelve_from, time_to)
        if groupname == 0:
            group_sql = ""
        else:
            group_sql = "and sale_charger in (select username from auth_user where id in (select user_id from suplychain_flashsale_myuser where group_id = {0}))".format(
                str(groupname))
        if len(search_text) > 0:
            search_text = str(search_text)
            product_sql = "select A.id,A.product_name,A.outer_id,A.pic_path,B.outer_id as outer_sku_id,B.quantity,B.properties_alias,B.id as sku_id,C.exist_stock_num from " \
                          "(select id,name as product_name,outer_id,pic_path from " \
                          "shop_items_product where outer_id like '%%{0}%%' or name like '%%{0}%%' ) as A " \
                          "left join (select id,product_id,outer_id,properties_alias,quantity from shop_items_productsku where status!='delete') as B " \
                          "on A.id=B.product_id left join flash_sale_product_sku_detail as C on B.id=C.product_sku".format(
                search_text)
        else:
            product_sql = "select A.id,A.product_name,A.outer_id,A.pic_path,B.outer_id as outer_sku_id,B.quantity,B.properties_alias,B.id as sku_id,C.exist_stock_num from " \
                          "(select id,name as product_name,outer_id,pic_path from " \
                          "shop_items_product where  sale_time='{0}' " \
                          "and status!='delete' {1}) as A " \
                          "left join (select id,product_id,outer_id,properties_alias,quantity from shop_items_productsku where status!='delete') as B " \
                          "on A.id=B.product_id left join flash_sale_product_sku_detail as C on B.id=C.product_sku".format(
                target_date, group_sql)
        ding_huo_sql = "select B.outer_id,B.chichu_id,sum(if(A.status='草稿' or A.status='审核',B.buy_quantity,0)) as buy_quantity,sum(if(A.status='7',B.buy_quantity,0)) as sample_quantity," \
                       "sum(if(status='5' or status='6' or status='有问题' or status='验货完成' or status='已处理',B.arrival_quantity,0)) as arrival_quantity,B.effect_quantity,A.status" \
                       " from (select id,status from suplychain_flashsale_orderlist where status not in ('作废') and created between '{0}' and '{1}') as A " \
                       "left join (select orderlist_id,outer_id,chichu_id,buy_quantity,arrival_quantity,(buy_quantity-non_arrival_quantity) as effect_quantity " \
                       "from suplychain_flashsale_orderdetail) as B on A.id=B.orderlist_id group by outer_id,chichu_id".format(
            shelve_from, query_time)
        sql = "select product.outer_id,product.product_name,product.outer_sku_id,product.pic_path,product.properties_alias," \
              "order_info.sale_num,ding_huo_info.buy_quantity,ding_huo_info.effect_quantity,product.sku_id,product.exist_stock_num," \
              "product.id,ding_huo_info.arrival_quantity,ding_huo_info.sample_quantity " \
              "from (" + product_sql + ") as product left join (" + order_sql + ") as order_info on product.outer_id=order_info.outer_id and product.outer_sku_id=order_info.outer_sku_id left join (" + ding_huo_sql + ") as ding_huo_info on product.outer_id=ding_huo_info.outer_id and product.sku_id=ding_huo_info.chichu_id"
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        trade_dict = {}
        total_more_num = 0
        total_less_num = 0
        for product in raw:
            sale_num = int(product[5] or 0)
            ding_huo_num = int(product[6] or 0)
            arrival_num = int(product[11] or 0)
            sample_num = int(product[12] or 0)
            ding_huo_status, flag_of_more, flag_of_less = functions.get_ding_huo_status(
                sale_num, ding_huo_num, int(product[9] or 0), sample_num,
                arrival_num)
            if flag_of_more:
                total_more_num += (sample_num + int(product[9] or 0) +
                                   ding_huo_num + arrival_num - sale_num)
            if flag_of_less:
                total_less_num += (sale_num - sample_num - int(product[9] or 0)
                                   - arrival_num - ding_huo_num)
            temp_dict = {"product_id": product[10],
                         "sku_id": product[2],
                         "product_name": product[1],
                         "pic_path": product[3],
                         "sale_num": sale_num or 0,
                         "sku_name": product[4],
                         "ding_huo_num": ding_huo_num,
                         "effect_num": product[7] or 0,
                         "ding_huo_status": ding_huo_status,
                         "sample_num": sample_num,
                         "flag_of_more": flag_of_more,
                         "flag_of_less": flag_of_less,
                         "sku_id": product[8],
                         "ku_cun_num": int(product[9] or 0),
                         "arrival_num": arrival_num}
            if dhstatus == u'0' or (
                        (flag_of_more or flag_of_less) and dhstatus == u'1') or (
                        flag_of_less and
                            dhstatus == u'2') or (flag_of_more and dhstatus == u'3'):
                if product[0] not in trade_dict:
                    trade_dict[product[0]] = [temp_dict]
                else:
                    trade_dict[product[0]].append(temp_dict)
        trade_dict = sorted(trade_dict.items(), key=lambda d: d[0])
        return render(
            request,
            "dinghuo/dailywork2.html",
              {"target_product": trade_dict,
               "shelve_from": target_date,
               "time_to": time_to,
               "searchDinghuo": query_time,
               'groupname': groupname,
               "dhstatus": dhstatus,
               "search_text": search_text,
               "total_more_num": total_more_num,
               "total_less_num": total_less_num})


class DailyDingHuoView2(View):
    def parseEndDt(self, end_dt):
        if not end_dt:
            dt = datetime.datetime.now()
            return datetime.datetime(dt.year, dt.month, dt.day, 23, 59, 59)
        if len(end_dt) > 10:
            return functions.parse_datetime(end_dt)
        return functions.parse_date(end_dt)

    def get(self, request):
        content = request.GET
        today = datetime.date.today()
        # 上架日期
        shelve_fromstr = content.get("df", None)
        # 订单结束时间
        shelve_to_str = content.get("dt", None)
        # 订货结束日期
        query_time_str = content.get("showt", None)
        # 订货开始日期
        dinghuo_begin_str = content.get("showt_begin", None)
        groupname = content.get("groupname", 0)
        dhstatus = content.get("dhstatus", '1')
        groupname = int(groupname)
        search_text = content.get("search_text", '').strip()
        target_date = today
        if shelve_fromstr:
            year, month, day = shelve_fromstr.split('-')
            target_date = datetime.date(int(year), int(month), int(day))
            """
            if target_date > today:
                target_date = today
            """
        shelve_from = datetime.datetime(target_date.year, target_date.month,
                                        target_date.day)
        time_to = self.parseEndDt(shelve_to_str)
        if time_to - shelve_from < datetime.timedelta(0):
            time_to = shelve_from + datetime.timedelta(1)
        query_time = self.parseEndDt(query_time_str)
        dinghuo_begin = self.parseEndDt(dinghuo_begin_str)
        task_id = task_ding_huo.delay(shelve_from, time_to, groupname, search_text,
                                      target_date, dinghuo_begin, query_time,
                                      dhstatus)
        return render(
            request,
            "dinghuo/daily_work.html",
              {"task_id": task_id,
               "shelve_from": target_date,
               "time_to": time_to,
               "searchDinghuo_end": query_time,
               'groupname': groupname,
               "dhstatus": dhstatus,
               "search_text": search_text,
               "searchDinghuo_begin": dinghuo_begin})


class DailyDingHuoOptimizeView(View):
    def parseEndDt(self, end_dt):
        if not end_dt:
            dt = datetime.datetime.now()
            return datetime.datetime(dt.year, dt.month, dt.day, 23, 59, 59)
        if len(end_dt) > 10:
            return functions.parse_datetime(end_dt)
        return functions.parse_date(end_dt)

    def get(self, request):
        content = request.GET
        today = datetime.date.today()
        shelve_fromstr = content.get("df", None)
        shelve_to_str = content.get("dt", None)
        query_time_str = content.get("showt", None)
        dinghuo_begin_str = content.get("showt_begin", None)
        groupname = content.get("groupname", 0)
        dhstatus = content.get("dhstatus", '1')
        groupname = int(groupname)
        search_text = content.get("search_text", '').strip()
        target_date = today
        if shelve_fromstr:
            year, month, day = shelve_fromstr.split('-')
            target_date = datetime.date(int(year), int(month), int(day))
            if target_date > today:
                target_date = today

        shelve_from = datetime.datetime(target_date.year, target_date.month,
                                        target_date.day)
        time_to = self.parseEndDt(shelve_to_str)
        if time_to - shelve_from < datetime.timedelta(0):
            time_to = shelve_from + datetime.timedelta(1)
        query_time = self.parseEndDt(query_time_str)
        dinghuo_begin = self.parseEndDt(dinghuo_begin_str)
        product_dict = get_product_dict(shelve_from, time_to, groupname,
                                        search_text, target_date, dinghuo_begin,
                                        query_time, dhstatus)
        return render(
            request,
            "dinghuo/daily_work_optimize.html",
              {"product_dict": product_dict,
               "shelve_from": target_date,
               "time_to": time_to,
               "searchDinghuo_end": query_time,
               'groupname': groupname,
               "dhstatus": dhstatus,
               "search_text": search_text,
               "searchDinghuo_begin": dinghuo_begin})


def get_product_dict(shelve_from, time_to, groupname, search_text, target_date,
                     dinghuo_begin, query_time, dhstatus):
    """非没有退款状态的，不算作销售数,没有之前的速度快"""
    if len(search_text) > 0:
        search_text = str(search_text)
        product_sql = "select A.id,A.product_name,A.outer_id,A.pic_path,B.outer_id as outer_sku_id,B.quantity,B.properties_alias,B.id as sku_id,C.exist_stock_num from " \
                      "(select id,name as product_name,outer_id,pic_path from " \
                      "shop_items_product where outer_id like '%%{0}%%' or name like '%%{0}%%' ) as A " \
                      "left join (select id,product_id,outer_id,properties_alias,quantity from shop_items_productsku where status!='delete') as B " \
                      "on A.id=B.product_id left join flash_sale_product_sku_detail as C on B.id=C.product_sku".format(
            search_text)
    else:
        product_sql = "select A.id,A.product_name,A.outer_id,A.pic_path,B.outer_id as outer_sku_id,B.quantity,B.properties_alias,B.id as sku_id,C.exist_stock_num from " \
                      "(select id,name as product_name,outer_id,pic_path from " \
                      "shop_items_product where  sale_time='{0}' " \
                      "and status!='delete') as A " \
                      "left join (select id,product_id,outer_id,properties_alias,quantity from shop_items_productsku where status!='delete') as B " \
                      "on A.id=B.product_id left join flash_sale_product_sku_detail as C on B.id=C.product_sku".format(
            target_date)

    cursor = connection.cursor()
    cursor.execute(product_sql)
    product_raw = cursor.fetchall()
    trade_dict = {}
    for one_product in product_raw:
        temp_dict = {"product_id": one_product[0],
                     "outer_sku_id": one_product[4],
                     "product_name": one_product[1],
                     "pic_path": one_product[3],
                     "sku_name": one_product[6],
                     "sku_id": one_product[7],
                     "ku_cun_num": int(one_product[8] or 0)}
        if one_product[2] not in trade_dict:
            trade_dict[one_product[2]] = [temp_dict]
        else:
            trade_dict[one_product[2]].append(temp_dict)
    trade_dict = sorted(trade_dict.items(), key=lambda d: d[0])
    # result_dict = {"trade_dict": trade_dict}
    return trade_dict


from flashsale.dinghuo import functions2view
from flashsale.dinghuo.models import OrderDetail, OrderDraft
from shopback.items.models import Product, ProductSku


class ShowPicView(View):
    def get_src_by_product(self, pro_id):
        a = Product.objects.filter(id=pro_id)
        if a.count() > 0:
            return a[0].pic_path
        else:
            return "ttt"

    def get(self, request, order_list_id):
        all_order = OrderDetail.objects.filter(orderlist__id=order_list_id)
        all_order_data = []
        temp_dict = {}
        for pro_id in all_order:
            if pro_id.product_id not in temp_dict:
                temp_dict[pro_id.product_id] = "in"
                all_order_data.append(self.get_src_by_product(
                    pro_id.product_id))
        return HttpResponse(",".join(all_order_data))


from rest_framework import generics
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response
from .. import function_of_task_optimize


class SkuAPIView(generics.ListCreateAPIView):
    """
        *   get:获取每个sku的销售情况（库存、model、detail）

    """
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        sku_id = request.GET.get("sku_id")
        dinghuo_begin = request.GET.get("dinghuo_begin")
        query_time = request.GET.get("query_time")
        time_to = request.GET.get("time_to")
        try:
            one_sku = ProductSku.objects.get(id=sku_id)
        except:
            return Response({"flag": "error"})
        sale_num = function_of_task_optimize.get_sale_num(
            one_sku.product.sale_time, time_to, one_sku.product.outer_id,
            one_sku.outer_id)
        ding_huo_num, sample_num, arrival_num = function_of_task_optimize.get_dinghuo_num(
            dinghuo_begin, query_time, one_sku.product.outer_id, one_sku.id)

        return Response({"flag": "done",
                         "sale_num": sale_num,
                         "ding_huo_num": ding_huo_num,
                         "arrival_num": arrival_num})


class AddDingHuoView(generics.ListCreateAPIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    permission_classes = (permissions.IsAuthenticated,)
    template_name = 'dinghuo/addpurchasedetail.html'

    def get(self, request):
        outer_ids = json.loads(request.GET.get('outer_ids') or '[]')
        productres = []
        for product in Product.objects.filter(outer_id__in=outer_ids):
            product_dict = model_to_dict(product)
            for sku in ProductSku.objects.filter(product_id=product.id).exclude(
                    status=u'delete'):
                sku_dict = model_to_dict(sku)
                sku_dict[
                    'wait_post_num'] = functions2view.get_lack_num_by_product(
                    product, sku)
                product_dict.setdefault('prod_skus', []).append(sku_dict)
            productres.append(product_dict)

        saleproduct_mapping = {}
        for saleproduct in SaleProduct.objects.filter(
                pk__in=map(lambda x: x['sale_product'], productres)):
            saleproduct_mapping[saleproduct.id] = saleproduct.supplier_sku or ''
        for item in productres:
            item['supplier_sku'] = saleproduct_mapping.get(item[
                                                               'sale_product']) or ''

        return Response({'productRestult': productres,
                         'drafts': OrderDraft.objects.all().filter(
                             buyer_name=request.user)})


class InstantDingHuoViewSet(viewsets.GenericViewSet):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    permission_classes = (permissions.IsAuthenticated,)
    template_name = 'dinghuo/instant_dinghuo.html'

    @list_route(methods=['get'])
    def advance(self, request):
        form = forms.AdvanceDingHuoForm(request.GET)
        if not form.is_valid():
            return Response({'error': ''}, template_name='dinghuo/advance_dinghuo.html')

        result = {
            'start_date': form.cleaned_attrs.start_date.strftime('%Y-%m-%d'),
            'end_date': form.cleaned_attrs.end_date.strftime('%Y-%m-%d')
        }
        if form.cleaned_attrs.start_date > form.cleaned_attrs.end_date:
            result['error'] = '参数错误'
            return Response(result, template_name='dinghuo/advance_dinghuo.html')

        start_date = form.cleaned_attrs.start_date
        end_date = form.cleaned_attrs.end_date
        schedule_ids = set()
        for m in SaleProductManage.objects.filter(sale_time__gte=start_date, sale_time__lte=end_date):
            schedule_ids.add(m.id)

        sale_product_ids = set()
        for d in SaleProductManageDetail.objects.filter(schedule_manage_id__in=list(schedule_ids),
                                                        today_use_status='normal'):
            sale_product_ids.add(d.sale_product_id)

        buyers_dict = {}
        suppliers_dict = {}
        saleproducts_dict = {}
        for s in SaleProduct.objects.select_related('sale_supplier').filter(id__in=list(sale_product_ids)):
            saleproducts_dict[s.id] = {
                'supplier_id': s.sale_supplier.id,
                'product_link': s.product_link
            }
            if s.sale_supplier.id not in suppliers_dict:
                supplier_dict = {
                    'id': s.sale_supplier.id,
                    'name': s.sale_supplier.supplier_name,
                    'buyer_id': 0,
                    'buyer_name': ''
                }
                orderlists = OrderList.objects.filter(
                    supplier_id=s.sale_supplier.id
                ).exclude(Q(status=OrderList.ZUOFEI) | Q(buyer__isnull=True)).order_by('-created')[:1]
                if orderlists:
                    orderlist = orderlists[0]
                    if orderlist.buyer_id:
                        buyer_id = orderlist.buyer_id
                        buyer_name = '%s%s' % (orderlist.buyer.last_name, orderlist.buyer.first_name)
                        buyer_name = buyer_name or orderlist.buyer.username
                        supplier_dict.update({
                            'buyer_id': buyer_id,
                            'buyer_name': buyer_name
                        })

                        if buyer_id not in buyers_dict:
                            buyers_dict[buyer_id] = buyer_name
                suppliers_dict[s.sale_supplier.id] = supplier_dict

        products_dict = {}
        for p in Product.objects.filter(sale_product__in=list(sale_product_ids), status='normal'):
            product_dict = {
                'id': p.id,
                'name': p.name,
                'outer_id': p.outer_id,
                'pic_path': '%s?imageMogr2/thumbnail/200x200/crop/200x200/format/jpg' % p.pic_path.strip(),
                'product_link': saleproducts_dict[p.sale_product]['product_link'],
                'skus': {}
            }
            supplier_id = saleproducts_dict[p.sale_product]['supplier_id']
            suppliers_dict[supplier_id].setdefault('products', []).append(product_dict)
            products_dict[p.id] = product_dict

        for s in ProductSku.objects.filter(product_id__in=products_dict.keys(), status='normal'):
            product_dict = products_dict[s.product_id]
            product_dict['skus'][s.id] = {
                'id': s.id,
                'properties_name': s.properties_name or s.properties_alias or '',
                'quantity': s.quantity
            }

        new_suppliers = []
        for supplier_id in sorted(suppliers_dict.keys()):
            supplier_dict = suppliers_dict[supplier_id]
            products = supplier_dict.get('products')
            if not products:
                continue
            for product in products:
                skus_dict = product['skus']
                product['skus'] = [skus_dict[k] for k in sorted(skus_dict.keys())]
            new_suppliers.append(supplier_dict)

        result['suppliers'] = new_suppliers
        result['buyers'] = [{'id': k, 'name': buyers_dict[k]} for k in sorted(buyers_dict.keys())]
        return Response(result, template_name='dinghuo/advance_dinghuo.html')

    def list(self, request):
        show_ab = int(request.GET.get('show_ab') or 0)

        min_datetime = datetime.datetime(1900, 1, 1)
        sale_stats = MergeOrder.objects.select_related('merge_trade').filter(
            merge_trade__type__in=[pcfg.SALE_TYPE, pcfg.DIRECT_TYPE,
                                   pcfg.REISSUE_TYPE, pcfg.EXCHANGE_TYPE],
            merge_trade__sys_status__in=
            [pcfg.WAIT_AUDIT_STATUS, pcfg.WAIT_PREPARE_SEND_STATUS,
             pcfg.WAIT_CHECK_BARCODE_STATUS, pcfg.WAIT_SCAN_WEIGHT_STATUS,
             pcfg.REGULAR_REMAIN_STATUS],
            sys_status=pcfg.IN_EFFECT).values(
            'outer_id', 'outer_sku_id').annotate(sale_num=Sum('num'), last_pay_time=Max('pay_time'))

        order_products = {}
        for s in sale_stats:
            skus = order_products.setdefault(s['outer_id'], {})
            skus[s['outer_sku_id']] = {
                'sale_quantity': s['sale_num'],
                'last_pay_time': s['last_pay_time']
            }

        sku_ids = set()
        products = {}
        for sku in ProductSku.objects.select_related('product').filter(
                product__outer_id__in=order_products.keys()):
            order_skus = order_products[sku.product.outer_id]
            if sku.outer_id in order_skus:
                sku_ids.add(sku.id)
                skus = products.setdefault(sku.product.id, {})
                sku_dict = {
                    'sale_quantity': 0,
                    'last_pay_time': min_datetime,
                    'buy_quantity': 0,
                    'arrival_quantity': 0,
                    'inferior_quantity': 0
                }
                sku_dict.update(order_skus.get(sku.outer_id) or {})
                skus[sku.id] = sku_dict

        dinghuo_stats = OrderDetail.objects \
            .exclude(orderlist__status__in=[OrderList.COMPLETED, OrderList.ZUOFEI]) \
            .values('product_id', 'chichu_id') \
            .annotate(buy_quantity=Sum('buy_quantity'), arrival_quantity=Sum('arrival_quantity'),
                      inferior_quantity=Sum('inferior_quantity'))
        for s in dinghuo_stats:
            product_id, sku_id = map(int, (s['product_id'], s['chichu_id']))
            sku_ids.add(sku_id)
            skus = products.setdefault(product_id, {})
            sku = skus.setdefault(sku_id, {'sale_quantity': 0, 'last_pay_time': min_datetime})
            sku.update({
                'buy_quantity': s['buy_quantity'],
                'arrival_quantity': s['arrival_quantity'],
                'inferior_quantity': s['inferior_quantity']
            })

        for sku in ProductSku.objects.filter(pk__in=list(sku_ids)):
            sku_dict = products[sku.product_id][sku.id]
            sku_dict.update({
                'id': sku.id,
                'quantity': sku.quantity,
                'properties_name': sku.properties_name or sku.properties_alias,
                'outer_id': sku.outer_id
            })

        saleproduct_ids = set()
        product_mapping = {}
        for product in Product.objects.filter(pk__in=products.keys()):
            saleproduct_ids.add(product.sale_product)
            product_mapping[product.id] = {
                'id': product.id,
                'name': product.name,
                'pic_path': '%s?imageView2/0/w/120' % product.pic_path.strip(),
                'outer_id': product.outer_id,
                'sale_product_id': product.sale_product
            }

        buyer_ids = set()
        supplier_mapping = {}
        saleproduct2supplier_mapping = {}
        for saleproduct in SaleProduct.objects.select_related(
                'sale_supplier').filter(pk__in=list(saleproduct_ids)):
            saleproduct2supplier_mapping[
                saleproduct.id] = saleproduct.sale_supplier.id
            if saleproduct.sale_supplier.id not in supplier_mapping:
                buyer_id = saleproduct.sale_supplier.buyer_id or 0
                if buyer_id:
                    buyer_ids.add(buyer_id)
                supplier_mapping[saleproduct.sale_supplier.id] = (
                    saleproduct.sale_supplier.supplier_name, buyer_id)

        buyer_mapping = {}
        for user in User.objects.filter(pk__in=list(buyer_ids)):
            buyer_name = '%s%s' % (user.last_name, user.first_name)
            buyer_mapping[user.id] = buyer_name or user.username

        buyers = {}
        suppliers = {}
        for product_id in sorted(products.keys(), reverse=True):
            if product_id not in product_mapping:
                continue
            skus = products[product_id]
            new_product = product_mapping[product_id]
            new_skus = []
            for sku in [skus[k] for k in sorted(skus.keys())]:
                effect_quantity = sku['quantity'] + sku[
                    'buy_quantity'] - sku['arrival_quantity'] - sku[
                                      'sale_quantity']
                if show_ab == 1 and effect_quantity == 0:
                    continue
                if show_ab == 2 and effect_quantity >= 0:
                    continue
                if show_ab == 3 and effect_quantity <= 0:
                    continue
                sku['effect_quantity'] = effect_quantity
                new_skus.append(sku)
            if not new_skus:
                continue
            new_product.update({
                'last_pay_time': max(filter(None, map(lambda x: x['last_pay_time'], new_skus)) or [min_datetime]),
                'skus': new_skus
            })
            sale_product_id = new_product['sale_product_id']
            supplier_id = saleproduct2supplier_mapping.get(sale_product_id) or 0
            if supplier_id not in suppliers:
                supplier_name, buyer_id = supplier_mapping.get(supplier_id) or (
                    '未知', 0)
                buyer_name = buyer_mapping.get(buyer_id) or '空缺'
                if buyer_id not in buyers:
                    buyers[buyer_id] = buyer_name
                supplier = {
                    'id': supplier_id,
                    'buyer_id': buyer_id,
                    'buyer_name': buyer_name,
                    'supplier_name': supplier_name,
                    'products': []
                }
                suppliers[supplier_id] = supplier
            else:
                supplier = suppliers[supplier_id]
            supplier['products'].append(new_product)

        new_suppliers = []
        pay_times = {}
        for k in sorted(suppliers.keys()):
            supplier = suppliers[k]
            if not supplier.get('products'):
                continue
            last_pay_time = max(map(lambda x: x['last_pay_time'], supplier['products']))
            if last_pay_time <= min_datetime:
                last_pay_date = '暂无销售'
            else:
                last_pay_date = last_pay_time.strftime('%Y-%m-%d')
            pay_times[int(last_pay_time.date().strftime('%Y%m%d'))] = last_pay_date
            supplier['last_pay_date'] = last_pay_date
            new_suppliers.append(supplier)

        last_pay_dates = []
        for k in sorted(pay_times.keys(), reverse=True):
            last_pay_dates.append(pay_times[k])

        new_buyers = []
        for k in sorted(buyers):
            new_buyers.append({
                'id': k,
                'name': buyers[k]
            })

        return Response({
            'suppliers': new_suppliers,
            'show_ab': show_ab,
            'pay_dates': last_pay_dates,
            'buyers': new_buyers
        })
