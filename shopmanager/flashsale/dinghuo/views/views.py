# coding:utf-8
import datetime
import json
import re
import time
from operator import itemgetter
from cStringIO import StringIO
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import F, Q, Sum, Count
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from rest_framework import generics, permissions, renderers, viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import exceptions
from core.options import log_action, ADDITION, CHANGE
from core.utils.csvutils import CSVUnicodeWriter
from core.xlmm_response import make_response, SUCCESS_RESPONSE
from core import xlmm_rest_exceptions
from flashsale.dinghuo import paramconfig as pcfg
from flashsale.dinghuo.models import (OrderDraft, OrderDetail, OrderList,
                                      InBound, InBoundDetail,
                                      OrderDetailInBoundDetail,
                                      RGDetail,
                                      SupplyChainDataStats)
from shopback.archives.models import DepositeDistrict
from shopback.categorys.models import ProductCategory
from shopback.items.models import Product, ProductSku, ProductStock, ProductLocation
from shopback.logistics.models import LogisticsCompany
from shopback.warehouse import WARE_CHOICES
from shopback.trades.models import PackageSkuItem, PackageOrder
from supplychain.supplier.models import SaleProduct, SaleSupplier
from .. import forms, functions, functions2view, models


def search_product(request):
    """搜索商品"""
    response = HttpResponse()
    response['Content-Type'] = "text/javascript"
    product_id_from_page = request.GET.get("searchtext", "")
    product_id_from_page = product_id_from_page.strip()
    product_result = Product.objects.filter(Q(
        outer_id__icontains=product_id_from_page) | Q(name__icontains=
                                                      product_id_from_page))
    product_list = functions.get_product_dict_from_product(product_result)
    data = json.dumps(product_list, cls=DjangoJSONEncoder)
    return HttpResponse(data)


@csrf_exempt
def init_draft(request):
    """初始化购物车"""
    user = request.user
    if request.method == "POST":
        post = request.POST
        product_counter = int(post["product_counter"])
        for i in range(1, product_counter + 1):
            product_id_index = "product_id_" + str(i)
            product_id = post[product_id_index]
            all_sku = ProductSku.objects.filter(product_id=product_id,
                                                status="normal")
            for pro_sku in all_sku:
                sku_quantity_index = product_id + "_tb_quantity_" + str(
                    pro_sku.id)
                sku_quantity = post[sku_quantity_index]
                mai_ru_jia_ge_index = product_id + "_tb_cost_" + str(pro_sku.id)
                mai_ru_jia_ge = post[mai_ru_jia_ge_index]
                mai_ru_jia_ge = float(mai_ru_jia_ge)
                if sku_quantity and mai_ru_jia_ge and mai_ru_jia_ge != 0 and sku_quantity != "0":
                    sku_quantity = int(sku_quantity)
                    mai_ru_jia_ge = float(mai_ru_jia_ge)
                    p1 = Product.objects.get(id=product_id)
                    draft_query = OrderDraft.objects.filter(
                        buyer_name=user,
                        product_id=product_id,
                        chichu_id=pro_sku.id)
                    if draft_query.count() > 0:
                        draft_query[0].buy_quantity = draft_query[
                                                          0].buy_quantity + sku_quantity
                        draft_query[0].save()
                    else:
                        current_time = datetime.datetime.now()
                        t_draft = OrderDraft(buyer_name=user,
                                             product_id=product_id,
                                             outer_id=p1.outer_id,
                                             buy_quantity=sku_quantity,
                                             product_name=p1.name,
                                             buy_unitprice=mai_ru_jia_ge,
                                             chichu_id=pro_sku.id,
                                             product_chicun=pro_sku.name,
                                             created=current_time)
                        t_draft.save()
        return HttpResponseRedirect("/sale/dinghuo/dingdan/")
    else:
        return HttpResponseRedirect("/sale/dinghuo/dingdan/")


@csrf_exempt
def new_order(request):
    """从购物车生成订单"""
    username = request.user

    buyer_name = '%s%s' % (request.user.last_name, request.user.first_name)
    buyer_name = buyer_name or request.user.username
    all_drafts = OrderDraft.objects.all().filter(buyer_name=username)
    express = OrderList.EXPRESS_CONPANYS
    if request.method == 'POST':
        post = request.POST
        type_of_order = post['type_of_order']
        p_district = post['p_district']
        costofems = post['costofems']
        if costofems == "":
            costofems = 0
        else:
            costofems = float(costofems)
        current_time = datetime.datetime.now()
        receiver = post['consigneeName']
        supplierId = post['supplierId']
        storehouseId = post['storehouseId']
        express_company = post['express_company']
        express_no = post['express_no']
        businessDate = datetime.datetime.now()
        remarks = post['remarks']
        amount = functions.cal_amount(username, costofems)
        orderlist = OrderList()
        orderlist.buyer_name = buyer_name
        orderlist.costofems = costofems * 100
        orderlist.receiver = receiver
        orderlist.express_company = express_company
        orderlist.express_no = express_no
        orderlist.supplier_name = supplierId
        orderlist.p_district = p_district
        orderlist.created = businessDate
        orderlist.updated = businessDate
        if len(remarks.strip()) > 0:
            orderlist.note = "-->" + request.user.username + " : " + remarks
        orderlist.status = pcfg.SUBMITTING
        if type_of_order == '2':
            orderlist.status = '7'
            already = OrderList.objects.filter(buyer_name=username,
                                               status='7',
                                               created=businessDate)
            if already.count() > 0:
                return HttpResponse('''<div style='position: absolute;top: 40%;
                        left: 35%;
                        width: 630px;
                        margin: -20px 0 0 -75px;
                        padding: 0 10px;
                        background: #eee;
                        line-height: 2.4;'>
                        您今天已经拍过样品的订货单了，请到订货单号为<a style='font-size: 40px' href='/sale/dinghuo/changedetail/{0}' target='_blank'>{0}</a>添加样品</div>'''
                                    .format(already[0].id))
        orderlist.order_amount = amount
        orderlist.save()

        drafts = OrderDraft.objects.filter(buyer_name=username)
        for draft in drafts:
            total_price = draft.buy_quantity * draft.buy_unitprice
            orderdetail1 = OrderDetail()
            orderdetail1.orderlist_id = orderlist.id
            orderdetail1.product_id = draft.product_id
            orderdetail1.outer_id = draft.outer_id
            orderdetail1.product_name = draft.product_name
            orderdetail1.product_chicun = draft.product_chicun
            orderdetail1.chichu_id = draft.chichu_id
            orderdetail1.buy_quantity = draft.buy_quantity
            orderdetail1.total_price = total_price
            orderdetail1.buy_unitprice = draft.buy_unitprice
            orderdetail1.created = current_time
            orderdetail1.updated = current_time
            orderdetail1.save()

        products_dict = {}
        for draft in drafts:
            pid = int(draft.product_id)
            products_dict[pid] = products_dict.get(pid, 0) + 1
        saleproducts_dict = {}
        for product in Product.objects.filter(id__in=products_dict.keys()):
            saleproducts_dict[product.sale_product] = saleproducts_dict.get(
                product.sale_product, 0) + products_dict[
                                                          product.id]
        suppliers_dict = {}
        for saleproduct in SaleProduct.objects.filter(
                id__in=saleproducts_dict.keys()):
            suppliers_dict[saleproduct.sale_supplier_id] = suppliers_dict.get(saleproduct.sale_supplier_id, 0) + \
                                                           saleproducts_dict[saleproduct.id]
        if suppliers_dict:
            supplier_id, _ = max(suppliers_dict.items(), key=itemgetter(1))
            if supplier_id:
                orderlist.supplier_id = supplier_id
        if not orderlist.supplier_id:
            ssp = SaleSupplier.objects.filter(supplier_name=orderlist.supplier_name).first()
            if not ssp:
                ssp = SaleSupplier.get_default_unrecord_supplier()
            orderlist.supplier = ssp

        orderlist.buyer_id = request.user.id
        orderlist.save()

        drafts.delete()
        log_action(request.user.id, orderlist, CHANGE, u'新建订货单')
        return HttpResponseRedirect("/sale/dinghuo/changedetail/" + str(
            orderlist.id))
    else:
        drafts = OrderDraft.objects.filter(buyer_name=username)
        supplier_name = ''
        products_dict = {}
        for draft in drafts:
            pid = int(draft.product_id)
            products_dict[pid] = products_dict.get(pid, 0) + 1
        saleproducts_dict = {}
        for product in Product.objects.filter(id__in=products_dict.keys()):
            saleproducts_dict[product.sale_product] = saleproducts_dict.get(
                product.sale_product, 0) + products_dict[
                                                          product.id]
        suppliers_dict = {}
        for saleproduct in SaleProduct.objects.filter(
                id__in=saleproducts_dict.keys()):
            suppliers_dict[saleproduct.sale_supplier_id] = suppliers_dict.get(saleproduct.sale_supplier_id, 0) + \
                                                           saleproducts_dict[saleproduct.id]
        if suppliers_dict:
            supplier_id, _ = max(suppliers_dict.items(), key=itemgetter(1))
            sale_suppliers = SaleSupplier.objects.filter(id=supplier_id)
            if sale_suppliers:
                sale_supplier = sale_suppliers[0]
                supplier_name = sale_supplier.supplier_name

    return render_to_response('dinghuo/shengchengorder.html',
                              {"OrderDraft": all_drafts,
                               "express": express,
                               'buyer_name': buyer_name,
                               'supplier_name': supplier_name},
                              context_instance=RequestContext(request))


def del_draft(request):
    username = request.user
    drafts = OrderDraft.objects.filter(buyer_name=username)
    drafts.delete()
    return HttpResponse("")


def add_purchase(request, outer_id):
    user = request.user
    order_dr_all = OrderDraft.objects.all().filter(buyer_name=user)
    product_res = []
    queryset = Product.objects.filter(status=Product.NORMAL,
                                      outer_id__icontains=outer_id)
    for p in queryset:
        product_dict = model_to_dict(p)
        product_dict['prod_skus'] = []
        guiges = ProductSku.objects.filter(product_id=p.id).exclude(
            status=u'delete')
        for guige in guiges:
            sku_dict = model_to_dict(guige)
            sku_dict['name'] = guige.name
            sku_dict['wait_post_num'] = functions2view.get_lack_num_by_product(
                p, guige)
            product_dict['prod_skus'].append(sku_dict)
        product_res.append(product_dict)
    return render_to_response("dinghuo/addpurchasedetail.html",
                              {"productRestult": product_res,
                               "drafts": order_dr_all},
                              context_instance=RequestContext(request))


@csrf_exempt
def data_chart(req):
    content = req.REQUEST
    today = datetime.date.today()
    start_time_str = content.get("df", None)
    end_time_str = content.get("dt", None)
    if start_time_str:
        year, month, day = start_time_str.split('-')
        start_date = datetime.date(int(year), int(month), int(day))
        if start_date > today:
            start_date = today
    else:
        start_date = today - datetime.timedelta(days=7)
    if end_time_str:
        year, month, day = end_time_str.split('-')
        end_date = datetime.date(int(year), int(month), int(day))
        if end_date > today:
            end_date = today
    else:
        end_date = today
    a_data = SupplyChainDataStats.objects.filter(
        group=u'采购A',
        stats_time__range=(start_date, end_date)).order_by('stats_time')
    b_data = SupplyChainDataStats.objects.filter(
        group=u'采购B',
        stats_time__range=(start_date, end_date)).order_by('stats_time')
    c_data = SupplyChainDataStats.objects.filter(
        group=u'采购C',
        stats_time__range=(start_date, end_date)).order_by('stats_time')

    return render_to_response("dinghuo/data_grape.html",
                              {"a_data": a_data,
                               "b_data": b_data,
                               "c_data": c_data,
                               "start_date": start_date,
                               "end_date": end_date},
                              context_instance=RequestContext(req))


@csrf_exempt
def plus_quantity(req):
    post = req.POST
    draft_id = post["draftid"]
    draft = OrderDraft.objects.get(id=draft_id)
    draft.buy_quantity = draft.buy_quantity + 1
    draft.save()
    return HttpResponse("OK")


@csrf_exempt
def plusordertail(req):
    post = req.POST
    orderdetailid = post["orderdetailid"]
    orderdetail = OrderDetail.objects.get(id=orderdetailid)
    orderlist = OrderList.objects.get(id=orderdetail.orderlist_id)
    OrderDetail.objects.filter(id=orderdetailid).update(
        buy_quantity=F('buy_quantity') + 1)
    OrderDetail.objects.filter(id=orderdetailid).update(
        total_price=F('total_price') + orderdetail.buy_unitprice)
    OrderList.objects.filter(id=orderdetail.orderlist_id).update(
        order_amount=F('order_amount') + orderdetail.buy_unitprice)
    log_action(req.user.id, orderlist, CHANGE, u'订货单{0}{1}{2}'.format(
        (u'加一件'), orderdetail.product_name, orderdetail.product_chicun))
    log_action(req.user.id, orderdetail, CHANGE, u'%s' % (u'加一'))
    return HttpResponse("OK")


@csrf_exempt
def minusquantity(req):
    post = req.POST
    draft_id = post["draftid"]
    draft = OrderDraft.objects.get(id=draft_id)
    draft.buy_quantity = draft.buy_quantity - 1
    draft.save()
    return HttpResponse("OK")


@csrf_exempt
def minusordertail(req):
    post = req.POST
    orderdetailid = post["orderdetailid"]
    orderdetail = OrderDetail.objects.filter(id=orderdetailid)
    if orderdetail.count() > 0:
        order_detail = orderdetail[0]
        order_list = OrderList.objects.get(id=order_detail.orderlist_id)
        OrderDetail.objects.filter(id=orderdetailid).update(
            buy_quantity=F('buy_quantity') - 1)
        OrderDetail.objects.filter(id=orderdetailid).update(
            total_price=F('total_price') - order_detail.buy_unitprice)
        OrderList.objects.filter(id=order_detail.orderlist_id).update(
            order_amount=F('order_amount') - order_detail.buy_unitprice)
        log_action(req.user.id, order_list, CHANGE, u'订货单{0}{1}{2}'.format(
            (u'减一件'), order_detail.product_name, order_detail.product_chicun))
        log_action(req.user.id, order_detail, CHANGE, u'%s' % (u'减一'))
        if order_detail.buy_quantity == 1:
            order_detail.delete()
            return HttpResponse("deleted")
        return HttpResponse("OK")
    else:
        return HttpResponse("false")


@csrf_exempt
def minusarrived(req):
    if not req.user.has_perm('dinghuo.change_orderdetail_quantity'):
        return HttpResponse(
            json.dumps({'error': True,
                        'msg': "权限不足"}),
            content_type='application/json')

    post = req.POST
    orderdetailid = post["orderdetailid"]
    orderdetail = OrderDetail.objects.get(id=orderdetailid)
    orderlist = OrderList.objects.get(id=orderdetail.orderlist_id)
    OrderDetail.objects.filter(id=orderdetailid).update(
        arrival_quantity=F('arrival_quantity') - 1)
    OrderDetail.objects.filter(id=orderdetailid).update(non_arrival_quantity=F(
        'buy_quantity') - F('arrival_quantity'))
    ProductStock.add_order_detail(orderdetail, -1)
    log_action(req.user.id, orderlist, CHANGE, u'订货单{0}{1}{2}'.format(
        (u'入库减一件'), orderdetail.product_name, orderdetail.product_chicun))
    log_action(req.user.id, orderdetail, CHANGE, u'%s' % (u'入库减一'))
    return HttpResponse("OK")


@csrf_exempt
def removedraft(req):
    post = req.POST
    draftid = post["draftid"]
    draft = OrderDraft.objects.get(id=draftid)
    draft.delete()
    return HttpResponse("OK")


@csrf_exempt
def viewdetail(req, orderdetail_id):
    orderlist = OrderList.objects.get(id=orderdetail_id)
    orderdetail = OrderDetail.objects.filter(orderlist_id=orderdetail_id)
    express = OrderList.EXPRESS_CONPANYS
    return render_to_response("dinghuo/orderdetail.html",
                              {"orderlist": orderlist,
                               "orderdetails": orderdetail,
                               "express": express},
                              context_instance=RequestContext(req))


@csrf_exempt
def detaillayer(req, orderdetail_id):
    orderlist = OrderList.objects.get(id=orderdetail_id)
    orderdetail = OrderDetail.objects.filter(orderlist_id=orderdetail_id)
    return render_to_response("dinghuo/layerdetail.html",
                              {"orderlist": orderlist,
                               "orderdetails": orderdetail},
                              context_instance=RequestContext(req))


@csrf_exempt
def changestatus(req):
    post = req.POST
    orderid = post["orderid"]
    status_text = post["func"]
    orderlist = OrderList.objects.get(id=orderid)
    orderlist.status = status_text
    orderlist.save()
    state = True
    if status_text == "审核":
        state = True
    else:
        state = False
    log_action(req.user.id, orderlist, CHANGE,
               u'%s订货单' % (state and u'审核' or u'作废'))
    return HttpResponse("OK")


@csrf_exempt
def setusertogroup(req):
    post = req.POST
    groupid = post.get("groupid", 0)
    uid = post["uid"]
    myuser = MyUser.objects.filter(user_id=int(uid))
    if myuser.count() > 0:
        myusertemp = myuser[0]
        myusertemp.group_id = int(groupid)
        myusertemp.save()
    else:
        MyUser(user_id=int(uid), group_id=int(groupid)).save()
    return HttpResponse("OK")


@csrf_exempt
def modify_order_list(req):
    post = req.POST
    order_list_id = post.get("orderlistid", 0)
    receiver = post['receiver']
    supplier_name = post['supplier_name']
    express_company = post['express_company']
    express_no = post['express_no']
    note = post.get('note', "")
    if len(note) > 0:
        note = "\n" + "-->" + datetime.datetime.now().strftime(
            '%m月%d %H:%M') + req.user.username + ":" + note
    order_amount = post['order_amount']
    try:
        orderlist = OrderList.objects.get(id=order_list_id)
        orderlist.receiver = receiver
        orderlist.supplier_name = supplier_name
        orderlist.express_company = express_company
        orderlist.express_no = express_no
        orderlist.note = orderlist.note + note
        orderlist.order_amount = order_amount
        orderlist.save()
        log_action(req.user.id, orderlist, CHANGE, u'修改订货单')
    except:
        return HttpResponse("False")
    return HttpResponse("OK")


@csrf_exempt
def add_detail_to_ding_huo(req):
    post = req.POST
    buy_quantity = post["buy_quantity"]
    buy_price = post["buy_price"]
    orderlistid = post["orderlistid"]
    sku_id = post["sku_id"]
    if len(buy_quantity.strip()) > 0 and len(buy_price.strip()) > 0 and len(
            orderlistid.strip()) > 0 and len(sku_id.strip()) > 0:
        buy_quantity, buy_price, orderlistid, sku_id = int(buy_quantity), float(
            buy_price), int(orderlistid), int(sku_id)
        pro_sku = ProductSku.objects.get(id=sku_id)
        product_id = pro_sku.product_id
        outer_id = pro_sku.product.outer_id
        product_name = pro_sku.product.name
        orderlist = OrderList.objects.get(id=orderlistid)
        product_chicun = pro_sku.properties_alias if len(
            pro_sku.properties_alias) > 0 else pro_sku.properties_name
        order = OrderDetail.objects.filter(orderlist_id=orderlistid,
                                           chichu_id=sku_id,
                                           buy_unitprice=buy_price)
        if order.count() > 0:
            ordertemp = order[0]
            ordertemp.buy_quantity = ordertemp.buy_quantity + buy_quantity
            ordertemp.total_price = ordertemp.total_price + buy_quantity * buy_price
            ordertemp.save()
            log_action(req.user.id, orderlist, CHANGE, u'订货单{0}{1}'.format(
                (u'加一件'), ordertemp.product_name))
        else:
            order_new = OrderDetail()
            order_new.orderlist_id = orderlistid
            order_new.product_id = product_id
            order_new.outer_id = outer_id
            order_new.product_name = product_name
            order_new.chichu_id = sku_id
            order_new.product_chicun = product_chicun
            order_new.buy_quantity = buy_quantity
            order_new.buy_unitprice = buy_price
            order_new.total_price = buy_price * buy_quantity
            order_new.save()
            log_action(req.user.id, orderlist, CHANGE, u'订货单{0}{1}'.format(
                (u'加一件'), order_new.product_name))
        return HttpResponse("OK")
    return HttpResponse("False")


@csrf_exempt
def changearrivalquantity(request):
    """
    修改入库存数量
    1、增加后为负数不予添加
    """
    if not request.user.has_perm('dinghuo.change_orderdetail_quantity'):
        return HttpResponse('{error: true, msg: "权限不足"}')

    post = request.POST
    order_detail_id = post.get("orderdetailid", "").strip()
    arrived_num = post.get("arrived_num", "0").strip()  # 获取即将入库的数量
    result = "{flag:false,num:0}"
    arrival_time = datetime.datetime.now()
    if len(arrived_num) > 0 and len(order_detail_id) > 0:
        arrived_num = int(arrived_num)
        order_detail_id = int(order_detail_id)
        order = OrderDetail.objects.get(id=order_detail_id)
        orderlist = OrderList.objects.get(id=order.orderlist_id)
        try:
            sku = ProductSku.objects.get(id=order.chichu_id)
            if sku.quantity + arrived_num < 0:
                return HttpResponse(result)
        except:
            return HttpResponse(result)
        order.arrival_quantity = order.arrival_quantity + arrived_num
        order.non_arrival_quantity = order.buy_quantity - order.arrival_quantity
        ProductStock.add_order_detail(order, arrived_num)
        order.arrival_time = arrival_time
        order.save()
        result = "{flag:true,num:" + str(order.arrival_quantity) + "}"
        log_action(request.user.id, orderlist, CHANGE,
                   u'订货单{0}{1}入库{2}件'.format(order.product_name,
                                             order.product_chicun, arrived_num))
        return HttpResponse(result)

    return HttpResponse(result)


@csrf_exempt
def change_inbound_quantity(request):
    """
    修改入仓单正次品数量
    1、增加后为负数不予添加
    """
    post = request.POST
    inbound_id = post.get("inbound_id", "").strip()
    order_list_id = post.get("order_list_id", "").strip()
    order_detail_id = post.get("order_detail_id", "").strip()
    change_num = int(post.get("num", 1))
    inbound = InBound.objects.get(id=inbound_id)
    order_list = OrderDetail.objects.get(id=order_detail_id)
    order_detail = OrderDetail.objects.get(id=order_detail_id)
    inbound_detail = inbound.details.filter(
        sku_id=order_detail.chichu_id).first()
    inbound_detail.arrival_quantity -= change_num
    inbound_detail.inferior_quantity += change_num
    inbound_detail.save()
    order_detail.arrival_quantity -= change_num
    order_detail.inferior_quantity += change_num
    order_detail.save()
    log_action(request.user.id, order_detail, CHANGE,
               u'审核入仓单SKU{0}次品{1}件'.format(order_detail.chichu_id, change_num))
    return HttpResponse("{isSuccess:true}")


class DailyDingHuoStatsView(View):
    def get(self, request):
        content = request.REQUEST
        daystr = content.get("day", None)
        today = datetime.date.today()
        year, month, day = today.year, today.month, today.day

        target_date = today
        if daystr:
            year, month, day = daystr.split('-')
            target_date = datetime.date(int(year), int(month), int(day))
            if target_date > today:
                target_date = today

        time_from = datetime.datetime(target_date.year, target_date.month,
                                      target_date.day)
        time_to = datetime.datetime(target_date.year, target_date.month,
                                    target_date.day, 23, 59, 59)

        prev_day = target_date - datetime.timedelta(days=1)
        next_day = None
        if target_date < today:
            next_day = target_date + datetime.timedelta(days=1)

        orderlists = OrderList.objects.exclude(status=u'作废').exclude(
            status=u'7').filter(created=target_date)
        orderlists_list = []
        for orderlist in orderlists:
            orderlist_dict = model_to_dict(orderlist)
            orderlist_dict['orderdetail'] = []

            orderdetails = OrderDetail.objects.filter(orderlist_id=orderlist.id)
            list = []
            for orderdetail in orderdetails:
                orderdetailouter_id = orderdetail.outer_id
                searchouterid = orderdetailouter_id[0:len(str(
                    orderdetailouter_id)) - 1]
                list.append(searchouterid)
            list = {}.fromkeys(list).keys()

            for listbean in list:
                temporder = orderdetails.filter(outer_id__icontains=listbean)
                tempproduct = Product.objects.filter(
                    outer_id__icontains=listbean)
                count_quantity = 0
                count_price = 0
                temp_dict = {}
                for order in temporder:
                    count_quantity += order.buy_quantity
                    count_price += order.total_price
                product_name = temporder[0].product_name.split('-')
                if tempproduct.count() > 0:
                    temp_dict['pic_path'] = tempproduct[0].pic_path
                else:
                    temp_dict['pic_path'] = ""
                temp_dict['product_name'] = product_name[0]
                temp_dict['outer_id_p'] = listbean
                temp_dict['quantity'] = count_quantity
                temp_dict['price'] = count_price
                orderlist_dict['orderdetail'].append(temp_dict)
            if orderlist.status == u"草稿":
                orderlist_dict['statusflag'] = True
            else:
                orderlist_dict['statusflag'] = False
            orderlists_list.append(orderlist_dict)
        return render_to_response("dinghuo/dailystats.html",
                                  {"orderlists_lists": orderlists_list,
                                   "prev_day": prev_day,
                                   "target_date": target_date,
                                   "next_day": next_day},
                                  context_instance=RequestContext(request))


import flashsale.dinghuo.utils as tools


class StatsByProductIdView(View):
    def getUserName(self, uid):
        try:
            return User.objects.get(pk=uid).username
        except:
            return 'none'

    def get(self, request, product_id):
        pro_bean = Product.objects.filter(id=product_id, status=Product.NORMAL)
        dinghuo_begin_str = request.GET.get("showt_begin")
        dinghuo_begin = ""
        order_details = OrderDetail.objects.none()
        if pro_bean.count() > 0:
            if not dinghuo_begin_str:
                dinghuo_begin = pro_bean[0].sale_time
            else:
                dinghuo_begin = tools.parse_date(dinghuo_begin_str)

            order_details = OrderDetail.objects.exclude(
                orderlist__status=u'作废').filter(product_id=product_id).filter(
                orderlist__created__gte=dinghuo_begin)

        return render_to_response("dinghuo/productstats.html",
                                  {"orderdetails": order_details,
                                   "dinghuo_begin": dinghuo_begin,
                                   "product_id": product_id},
                                  context_instance=RequestContext(request))


from flashsale.dinghuo.models_user import MyUser
from django.db import connection


class DailyWorkView(View):
    def parseEndDt(self, end_dt):
        if not end_dt:
            dt = datetime.datetime.now()
            return datetime.datetime(dt.year, dt.month, dt.day, 23, 59, 59)
        if len(end_dt) > 10:
            return functions.parse_datetime(end_dt)
        return functions.parse_date(end_dt)

    def get(self, request):
        content = request.REQUEST
        today = datetime.date.today()
        shelve_fromstr = content.get("df", None)
        shelve_to_str = content.get("dt", None)
        query_time_str = content.get("showt", None)
        groupname = content.get("groupname", 0)
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
        order_sql = "select id,outer_id,sum(num) as sale_num,pay_time from " \
                    "shop_trades_mergeorder where sys_status='IN_EFFECT' " \
                    "and merge_trade_id in (select id from shop_trades_mergetrade where type not in ('reissue','exchange') " \
                    "and status in ('WAIT_SELLER_SEND_GOODS','WAIT_BUYER_CONFIRM_GOODS','TRADE_BUYER_SIGNED','TRADE_FINISHED') " \
                    "and sys_status not in('INVALID','ON_THE_FLY') " \
                    "and id not in (select id from shop_trades_mergetrade where sys_status='FINISHED' and is_express_print=False))" \
                    "and gift_type !=4 " \
                    "and (pay_time between '{0}' and '{1}') " \
                    "and char_length(outer_id)>=9 " \
                    "and (left(outer_id,1)='9' or left(outer_id,1)='8' or left(outer_id,1)='1') " \
                    "group by outer_id".format(shelve_from, time_to)

        if groupname == 0:
            group_sql = ""
        else:
            group_sql = "and sale_charger in (select username from auth_user where id in (select user_id from suplychain_flashsale_myuser where group_id =" + str(
                groupname) + "))"
        if len(search_text) > 0:
            search_text = str(search_text)
            product_sql = "select id,name as product_name,outer_id,pic_path from " \
                          "shop_items_product where status='normal' and outer_id like '%%{0}%%' or name like '%%{0}%%'".format(
                search_text)
        else:
            product_sql = "select id,name as product_name,outer_id,pic_path,cost, agent_price,category_id from " \
                          "shop_items_product where  sale_time='{0}' and status!='delete' {1}".format(
                target_date, group_sql)
        sql = "select product.outer_id,product.product_name,product.pic_path," \
              "order_info.sale_num,product.id,product.cost,product.agent_price,product.category_id " \
              "from (" + product_sql + ") as product left join (" + order_sql + ") as order_info on product.outer_id=order_info.outer_id "

        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        trade_dict = {}

        for product in raw:
            sale_num = int(product[3] or 0)
            outer_id = product[0]
            cost = product[5]
            agent_price = product[6]
            category = product[7]
            temp_dict = {"outer_id": product[0],
                         "product_id": product[4],
                         "product_name": product[1].split("/")[0],
                         "pic_path": product[2],
                         "sale_num": sale_num or 0,
                         "cost": cost,
                         "agent_price": agent_price,
                         "category": category}
            pro_id = outer_id[0:len(outer_id) - 1]
            if pro_id not in trade_dict:
                trade_dict[pro_id] = temp_dict
            else:
                trade_dict[pro_id]['sale_num'] += sale_num
        trade_dict = sorted(trade_dict.items(),
                            key=lambda d: d[1]['sale_num'],
                            reverse=True)
        return render_to_response("dinghuo/dailywork.html",
                                  {"target_product": trade_dict,
                                   "shelve_from": target_date,
                                   "time_to": time_to,
                                   "searchDinghuo": query_time,
                                   'groupname': groupname,
                                   "search_text": search_text},
                                  context_instance=RequestContext(request))


def get_category(category):
    if not category.parent_cid:
        return unicode(category.name)
    try:
        p_cat = category.__class__.objects.get(cid=category.parent_cid).name
    except:
        p_cat = u'--'
    return p_cat


class ProductCategoryAPIView(generics.ListCreateAPIView):
    """

    """
    renderer_classes = (renderers.JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        product = request.GET.get("product")
        category = request.GET.get("category")
        kucun = 0
        all_product = Product.objects.filter(status=Product.NORMAL,
                                             outer_id__startswith=product)
        for one_product in all_product:
            kucun += one_product.collect_num
        try:
            category_bean = ProductCategory.objects.get(cid=category)
            group = get_category(category_bean)
            category = category_bean.__unicode__()
        except:
            return Response({"flag": "error"})
        return Response({"flag": "done",
                         "group": group,
                         "category": category,
                         "stock": kucun})


class PendingDingHuoViewSet(viewsets.GenericViewSet):
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = models.OrderList.objects.all()
    template_name = 'dinghuo/pending_dinghuo.html'

    def list(self, request, *args, **kwargs):
        from common.utils import get_admin_name

        if not re.search(r'application/json', request.META['HTTP_ACCEPT']):
            return Response()

        now = datetime.datetime.now()
        items = []

        status_mapping = dict(models.OrderList.ORDER_PRODUCT_STATUS)
        for order_list in models.OrderList.objects \
                .exclude(status__in=[models.OrderList.COMPLETED, models.OrderList.ZUOFEI, models.OrderList.CLOSED]) \
                .order_by('-updated'):
            buyer_name = ''
            if order_list.buyer_id and order_list.buyer:
                buyer_name = get_admin_name(order_list.buyer)

            items.append({
                'id': order_list.id,
                'receiver': buyer_name,
                'order_amount': round(order_list.order_amount, 2),
                'supplier_name': order_list.supplier_name,
                'supplier_shop': order_list.supplier_shop,
                'status': order_list.status,
                'pay_status': order_list.pay_status,
                'p_district': order_list.p_district,
                'created': order_list.created,
                'updated': {
                    'display': order_list.updated.strftime('%Y-%m-%d %H:%M:%S'),
                    'timestamp': time.mktime(order_list.updated.timetuple())
                },
                'memo': order_list.note.replace('\r\n', '<br>').replace('\n',
                                                                        '<br>')
            })

        order_stat_mapping = {}
        for stat in models.OrderDetail.objects \
                .filter(orderlist_id__in=map(lambda x: x['id'], items)) \
                .values('orderlist_id') \
                .annotate(model_count=Count('outer_id', distinct=True), quantity=Sum('buy_quantity')):
            order_stat_mapping[stat['orderlist_id']] = stat

        for item in items:
            item['up_to_today'] = (now.date() - item['created']).days
            item['created'] = item['created'].strftime('%Y-%m-%d')
            if item['p_district'] == '3':
                item['warehouse'] = '广州'
            else:
                item['warehouse'] = '上海'
            if item['status'] in status_mapping.keys():
                item['status'] = status_mapping[item['status']]
            order_list_stat = order_stat_mapping.get(item['id']) or {}
            item['model_count'] = order_list_stat.get('model_count') or 0
            item['quantity'] = order_list_stat.get('quantity') or 0
            item['pay_status'] = item.get('pay_status') or '正常'
        return Response({'data': items})


class DingHuoOrderListViewSet(viewsets.GenericViewSet):
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer, renderers.BrowsableAPIRenderer)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = models.OrderList.objects.all()

    EXPRESS_NO_SPLIT_PATTERN = re.compile(r'\s+|,|，')
    MEMO_TPL = '编码:%(outer_id)s 商品名:%(product_name)s 规格:%(properties_name)s %(msg)s'

    ORDERDETAIL_OP_LOG_TPL = '订货单明细ID:%(id)d %(msg)s'
    ORDERDETAIL_INBOUNDDETAIL_OP_LOG_TPL = '入库操作记录ID:%(id)d %(msg)s'
    INBOUNDDETAIL_OP_LOG_TPL = '入库明细ID:%(id)d %(msg)s'
    ORDERLIST_OP_LOG_TPL = '订货单ID:<a href="/sale/dinghuo/changedetail/%(id)d/" target="_blank">%(id)d</a> %(msg)s'
    INBOUND_OP_LOG_TPL = '入仓单ID:%(id)d %(msg)s'

    DISTRICT_REGEX = re.compile(
        '^(?P<pno>[a-zA-Z0-9=]+)-(?P<dno>[a-zA-Z0-9]+)?$')

    @classmethod
    def get_username(cls, user):
        last_name = user.last_name
        first_name = user.first_name
        if len(last_name) > 1:
            names = [first_name, last_name]
        else:
            names = [last_name, first_name]
        return ''.join(filter(None, names)) or user.username

    @classmethod
    def update_orderlist(cls, request, orderlist_ids, op_logs):
        orderlist_status_dict = dict(OrderList.ORDER_PRODUCT_STATUS)
        for orderlist in OrderList.objects.filter(id__in=list(orderlist_ids)):
            flag_inferior = 0
            flag_lack = 0
            flag_arrival = 0
            for orderdetail in orderlist.order_list.all():
                if orderdetail.inferior_quantity + orderdetail.arrival_quantity < orderdetail.buy_quantity:
                    flag_lack = 1
                if orderdetail.arrival_quantity < orderdetail.buy_quantity and orderdetail.inferior_quantity > 0:
                    flag_inferior = 1
                if orderdetail.arrival_quantity > 0:
                    flag_arrival = 1

            status = None
            if flag_inferior and flag_lack:
                status = OrderList.QUESTION
            elif flag_inferior:
                status = OrderList.CIPIN
            elif flag_lack and flag_arrival:
                status = OrderList.QUESTION_OF_QUANTITY
            else:
                if flag_arrival > 0:
                    if orderlist.is_postpay:
                        status = OrderList.TO_PAY
                    else:
                        status = OrderList.CLOSED
                else:
                    status = OrderList.APPROVAL
            if status:
                orderlist.status = status
                if orderlist.note:
                    orderlist.note += '\n'
                orderlist.note += '-->%s%s: %s' % (
                    datetime.datetime.now().strftime('%m月%d %H:%M'),
                    request.user.username, orderlist_status_dict[status])
                orderlist.save()

                msg = u'更新状态为 %s' % orderlist_status_dict[status]
                log_action(request.user.id, orderlist, CHANGE, msg)
                op_logs.append(cls.ORDERLIST_OP_LOG_TPL % {
                    'id': orderlist.id,
                    'msg': msg
                })

    @classmethod
    def update_inbound(cls, request, inbound, inbound_skus_dict, op_logs):
        username = cls.get_username(request.user)
        now = datetime.datetime.now()

        # 过滤无效输入
        for k in inbound_skus_dict.keys():
            inbound_sku_dict = inbound_skus_dict[k]
            if not (inbound_sku_dict['arrival_quantity'] or
                        inbound_sku_dict['inferior_quantity']):
                inbound_skus_dict.pop(k, False)

        if inbound_skus_dict:
            inbound.status = InBound.PENDING
            op_logs.append(cls.INBOUND_OP_LOG_TPL % {'id': inbound.id,
                                                     'msg': '设为待处理'})
            log_action(request.user.id, inbound, CHANGE, '待处理')
            if inbound.memo:
                inbound.memo += '\n'
            tmp = []
            for sku_id in sorted(inbound_skus_dict.keys()):
                tmp.append('-->%s %s: SKU(%d)输入大于待入库数, 系统设为待处理' %
                           (now.strftime('%m月%d %H:%M'), username, sku_id))
            inbound.memo += '\n'.join(tmp)
        else:
            inbound.status = InBound.NORMAL
            op_logs.append(cls.INBOUND_OP_LOG_TPL % {'id': inbound.id,
                                                     'msg': '设为正常'})
            log_action(request.user.id, inbound, CHANGE, '正常')

        inbounddetail_ids = set()
        for detail in inbound.details.filter(Q(arrival_quantity__gt=0) | Q(
                inferior_quantity__gt=0)).exclude(sku__isnull=True):
            inbounddetail_ids.add(detail.id)

        orderlist_ids = set()
        for record in OrderDetailInBoundDetail.objects.select_related(
                'orderdetail').filter(
            inbounddetail_id__in=list(inbounddetail_ids),
            status=OrderDetailInBoundDetail.NORMAL):
            orderlist_ids.add(record.orderdetail.orderlist_id)
        inbound.orderlist_ids = sorted(list(orderlist_ids))
        inbound.save()

    @list_route(methods=['get'])
    def do_memo(self, request):
        username = self.get_username(request.user)
        now = datetime.datetime.now()
        content = request.GET.get('content') or ''
        if not content:
            return Response({'memo': ''})
        memo = '-->%s %s: %s' % (now.strftime('%m月%d %H:%M'), username, content)
        return Response({'memo': memo})

    @list_route(methods=['get'])
    def suggest_district(self, request):
        product_id = int(request.GET.get('product_id'))
        district = ''
        stats = {}
        for product_location in ProductLocation.objects.filter(
                product_id=product_id):
            k = str(product_location.district)
            stats[k] = stats.setdefault(k, 0) + 1
        if stats:
            district, _ = max(stats.items(), key=lambda x: x[1])
        if district:
            return Response({'district': district})

        the_product = Product.objects.get(id=product_id)
        product_ids = []
        for product in Product.objects.filter(
                sale_product=the_product.sale_product):
            product_ids.append(product.id)

        stats = {}
        for product_location in ProductLocation.objects.filter(
                product_id__in=product_ids):
            k = str(product_location.district)
            stats[k] = stats.setdefault(k, 0) + 1

        if stats:
            district, _ = max(stats.items(), key=lambda x: x[1])
        return Response({'district': district})

    @detail_route(methods=['post'])
    def delete_detail(self, request, pk):
        detail_id = int(request.POST.get('detail_id') or 0)
        if detail_id:
            InBoundDetail.objects.get(id=detail_id).delete()
        return Response('OK')

    @list_route(methods=['get'])
    def districts(self, request):
        districts = DepositeDistrict.objects.all().order_by('id')
        return Response([str(x) for x in districts])

    @detail_route(methods=['post'])
    def change_buyer(self, request, pk):
        buyer_id = int(request.POST.get('buyer_id') or 0)
        models.OrderList.objects.filter(id=pk).update(buyer=buyer_id)
        return Response(buyer_id)

    @detail_route(methods=['post'])
    def create_bill(self, request, pk):
        pay_tool = request.REQUEST.get("pay_tool", None)
        orderlist = get_object_or_404(OrderList, id=pk)
        if orderlist.bill:
            return Response({"res": False, "data": [], "desc": u"此订货单已经创建过账单了。"})
        pay_way = request.REQUEST.get("pay_way", None)
        plan_amount = request.REQUEST.get("money", None)
        transcation_no = request.REQUEST.get("transcation_no", None)
        receive_account = request.REQUEST.get("receive_account", None)
        receive_name = request.REQUEST.get("receive_name", None)
        pay_taobao_link = request.REQUEST.get("pay_taobao_link", None)
        amount = .0
        from flashsale.finance.models import Bill, BillRelation
        if int(pay_way) == OrderList.PC_POD_TYPE:
            status = Bill.STATUS_PENDING
        else:  # 判断如果pay_way是货到付款，那么bill状态是延期付款，否则是待付款状态
            status = Bill.STATUS_DELAY
        if pay_way == Bill.SELF_PAY and float(plan_amount) == 0:
            orderlist.set_stage_receive(pay_way)
            return Response({"res": True, "data": [], "desc": ""})
        if float(plan_amount) == 0:
            return Response({"res": False, "data": [], "desc": u"计划金额不能为0"})
        if int(pay_tool) == Bill.SELF_PAY:
            status = Bill.STATUS_COMPLETED
            plan_amount = plan_amount
        pay_method = pay_tool
        if pay_method == '0':
            return Response({"res": False, "data": [], "desc": u"请选择支付方式"})
        try:
            bill = Bill.create([orderlist], Bill.PAY, status, pay_method, plan_amount, amount, orderlist.supplier,
                               user_id=request.user.id, receive_account=receive_account, receive_name=receive_name,
                               pay_taobao_link=pay_taobao_link, transcation_no=transcation_no)
        except:
            return Response({"res": False, "data": [], "desc": u"无法写入财务记录"})

        if int(pay_way) == OrderList.PC_POD_TYPE:
            orderlist.set_stage_pay(pay_way)
        else:
            orderlist.set_stage_receive(pay_way)
        return Response({"res": True, "data": [], "desc": ""})

    @detail_route(methods=['post'])
    def edit_bill(self, request, pk):
        pay_tool = request.REQUEST.get("pay_tool", None)
        # orderlist = get_object_or_404(OrderList, id=pk)
        pay_way = request.REQUEST.get("pay_way", None)
        plan_amount = request.REQUEST.get("money", None)
        transcation_no = request.REQUEST.get("transcation_no", None)
        receive_account = request.REQUEST.get("receive_account", None)
        receive_name = request.REQUEST.get("receive_name", None)
        pay_taobao_link = request.REQUEST.get("pay_taobao_link", None)
        from flashsale.finance.models import Bill, BillRelation
        bill = get_object_or_404(Bill, id=pk)
        orderlist = bill.get_orderlist()
        if bill.status in [Bill.STATUS_DEALED, Bill.STATUS_COMPLETED]:
            return Response({"res": False, "data": [], "desc": u"订单已支付不能编辑"})
        if pay_way == Bill.SELF_PAY:
            return Response({"res": False, "data": [], "desc": u"无法选择自付"})
        if float(plan_amount) == 0:
            return Response({"res": False, "data": [], "desc": u"计划金额不能为0"})
        pay_method = pay_tool
        if pay_method == '0':
            return Response({"res": False, "data": [], "desc": u"请选择支付方式"})
        try:
            bill.pay_method = pay_method
            bill.status = Bill.STATUS_PENDING
            bill.plan_amount = plan_amount
            bill.supplier = orderlist.supplier
            bill.receive_account = receive_account
            bill.receive_name = receive_name
            bill.pay_taobao_link = pay_taobao_link
            bill.transcation_no = transcation_no
            bill.save()
        except:
            return Response({"res": False, "data": [], "desc": u"无法写入财务记录"})
        return Response({"res": True, "data": [], "desc": ""})

    @detail_route(methods=['post'])
    def set_stage_state(self, request, pk):
        from flashsale.finance.models import Bill, BillRelation
        from django.db.models import F
        orderlist = get_object_or_404(OrderList, pk=pk)
        sum = 0
        for i in orderlist.order_list.order_by('id'):
            sum += i.buy_unitprice * i.need_arrival_quantity
        if sum != 0:
            bill_id = BillRelation.objects.filter(object_id=orderlist.id, type=1).first().bill_id
            if bill_id and orderlist.bill_method == OrderList.PC_COD_TYPE:
                Bill.objects.filter(id=bill_id).update(plan_amount=F('plan_amount') - sum, status=Bill.STATUS_PENDING)
                orderlist.stage = OrderList.STAGE_STATE
                orderlist.save()
                return Response({"res": True, "data": [sum], "desc": ""})
            bill = Bill(type=Bill.RECEIVE, status=Bill.STATUS_PENDING, creater_id=request.user.id, plan_amount=sum,
                        pay_method=Bill.TAOBAO_PAY, supplier=orderlist.supplier)
            bill.save()
            lack_dict = {orderlist.id: BillRelation.TYPE_DINGHUO_RECEIVE}
            bill.relate_to([orderlist], lack_dict)
        orderlist.set_stage_state()
        return Response({"res": True, "data": [sum], "desc": ""})

    @detail_route(methods=['get'])
    def get_back_money(self, request, pk):
        from flashsale.finance.models import BillRelation
        billrelation = BillRelation.objects.filter(object_id=pk, type=2).first()
        if not billrelation:
            return Response({"res": True, "data": [], "desc": "没有回款记录"})
        plan_amount = billrelation.bill.plan_amount
        transcation_no = billrelation.bill.transcation_no
        note = billrelation.bill.note
        return Response({"res": True, "data": [plan_amount, transcation_no, note], "desc": ""})

    @detail_route(methods=['post'])
    def set_bill_dealed(self, request, pk):
        plan_amount = request.REQUEST.get("amount")
        transaction_no = request.REQUEST.get("transaction_no")
        attachment = request.REQUEST.get("attachment")
        note = request.REQUEST.get("note")
        from flashsale.finance.models import Bill, BillRelation
        orderlist = OrderList.objects.get(id=pk)
        if orderlist.bill_method == OrderList.PC_COD_TYPE:
            return Response({"res": False, "data": [pk], "desc": "货到付款不会生成回款记录,回款金额已在付款中扣除"})
        bill = BillRelation.objects.get(object_id=pk, type=2).bill
        bill.plan_amount = plan_amount
        bill.transcation_no = transaction_no
        bill.status = Bill.STATUS_DEALED
        bill.note = note
        bill.attachment = attachment
        bill.save()
        # billrelation.bill.update(plan_amount=plan_amount,transcation_no=transaction_no,note=note,status=Bill.STATUS_DEALED)
        return Response({"res": True, "data": [pk], "desc": ""})

    # @detail_route(methods=['post'])
    # def set_stage_receive(self, request, pk):
    #     orderlist = get_object_or_404(OrderList, pk=pk)
    #     orderlist.set_stage_receive()
    #     return Response(True)

    @detail_route(methods=['post'])
    def set_stage_complete(self, request, pk):
        orderlist = get_object_or_404(OrderList, pk=pk)
        orderlist.set_stage_complete()
        return Response(True)

    @detail_route(methods=['post'])
    def set_stage_delete(self, request, pk):
        orderlist = get_object_or_404(OrderList, pk=pk)
        orderlist.set_stage_delete()
        return Response(True)

    @detail_route(methods=['post'])
    def press_order(self, request, pk):
        orderlist = get_object_or_404(OrderList, pk=pk)
        desc = request.POST.get("desc", '')
        if desc:
            orderlist.press(desc)
        return Response(True)

    @detail_route(methods=['post'])
    def cancel(self, request, pk):
        inbounds = InBound.objects.filter(id=pk)[:1]
        if not inbounds:
            return Response({'msg': '入仓单不存在'})
        op_logs = []
        inbound = inbounds[0]
        orderlist_ids = set()
        for inbound_detail in inbound.details.filter(
                status=InBoundDetail.NORMAL):
            for record in inbound_detail.records.filter(
                    status=OrderDetailInBoundDetail.NORMAL):
                if record.arrival_quantity:
                    record.orderdetail.arrival_quantity -= record.arrival_quantity
                    msg = '到货数-%d' % record.arrival_quantity
                    op_logs.append(self.ORDERDETAIL_OP_LOG_TPL %
                                   {'id': record.orderdetail.id,
                                    'msg': msg})
                    log_action(request.user.id, record.orderdetail, CHANGE, msg)
                if record.inferior_quantity:
                    record.orderdetail.inferior_quantity -= record.inferior_quantity
                    msg = '次品数-%d' % record.arrival_quantity
                    op_logs.append(self.ORDERDETAIL_OP_LOG_TPL %
                                   {'id': record.orderdetail.id,
                                    'msg': msg})
                    log_action(request.user.id, record.orderdetail, CHANGE, msg)

                orderlist_ids.add(record.orderdetail.orderlist_id)
                record.orderdetail.save()

                record.status = OrderDetailInBoundDetail.INVALID
                record.save()
                op_logs.append(self.ORDERDETAIL_INBOUNDDETAIL_OP_LOG_TPL %
                               {'id': record.id,
                                'msg': '设为无效'})
            if inbound_detail.arrival_quantity > 0:
                inbound_detail.sku.quantity -= inbound_detail.arrival_quantity
                inbound_detail.sku.save()
                log_action(request.user.id, inbound_detail.sku, CHANGE,
                           u'作废入仓单%d: 更新库存%+d' %
                           (inbound.id, 0 - inbound_detail.arrival_quantity))

            inbound_detail.arrival_quantity = 0
            inbound_detail.inferior_quantity = 0
            inbound_detail.save()
            msg = '更新 到货数%d 次品数%d' % (0, 0)
            op_logs.append(self.INBOUNDDETAIL_OP_LOG_TPL %
                           {'id': inbound_detail.id,
                            'msg': msg})
            log_action(request.user.id, inbound_detail, CHANGE, msg)

        self.update_orderlist(request, orderlist_ids, op_logs)
        inbound.status = InBound.INVALID
        inbound.orderlist_ids = []
        inbound.save()
        op_logs.append(self.INBOUND_OP_LOG_TPL % {'id': inbound.id,
                                                  'msg': '设为无效'})
        log_action(request.user.id, inbound, CHANGE, u'设为无效')
        log_action(request.user.id, inbound, CHANGE,
                   mark_safe('\n'.join(op_logs)))
        return Response({'msg': ''.join(map(lambda x: '<p>%s</p>' % x, op_logs))
                         })

    @list_route(methods=['post'])
    def edit_supplier_inbound(self, request):
        form = forms.EditInBoundForm(request.POST)
        if not form.is_valid():
            return Response({'error': '参数错误'})

        if not form.cleaned_attrs.inbound_id:
            return Response({'error': '入仓单不存在'})

        inbounds = InBound.objects.filter(id=form.cleaned_attrs.inbound_id)[:1]
        if not inbounds:
            return Response({'error': '入仓单不存在'})
        inbound = inbounds[0]

        if inbound.status == InBound.INVALID:
            return Response({'error': '无效入仓单不能修改'})

        inbound.images = json.loads(form.cleaned_attrs.images or '')
        if form.cleaned_attrs.memo:
            inbound.memo = form.cleaned_attrs.memo
        inbound.save()
        log_action(request.user.id, inbound, CHANGE, u'修改')

        inbound_skus = json.loads(form.cleaned_attrs.skus)
        if not inbound_skus:
            return Response({'error': '请点击作废按钮'})
        inbound_skus_dict = {int(x['sku_id']): x for x in inbound_skus}

        if not any([x['arrival_quantity'] + x['inferior_quantity']
                    for x in inbound_skus_dict.values()]):
            return Response({'error': '请点击作废按钮'})

        details = json.loads(form.cleaned_attrs.details)
        op_logs = []
        skus_dict = {}
        for sku in ProductSku.objects.select_related('product').filter(
                id__in=inbound_skus_dict.keys()):
            skus_dict[sku.id] = {
                'product_id': sku.product.id,
                'sku_id': sku.id,
                'outer_id': sku.product.outer_id,
                'product_name': sku.product.name,
                'properties_name': sku.properties_name or
                                   sku.properties_alias or '',
                'quantity': sku.quantity
            }

        inbound_details = {}
        for inbound_detail in inbound.details.filter(
                status=InBoundDetail.NORMAL):
            inbound_details[inbound_detail.sku_id] = inbound_detail

        orderlist_ids = set()
        for sku_id in inbound_skus_dict.keys():
            inbound_sku_dict = inbound_skus_dict[sku_id]
            sku_dict = skus_dict.get(sku_id)
            if not sku_dict:
                continue
            product_id = sku_dict['product_id']
            outer_id = sku_dict['outer_id']
            product_name = sku_dict['product_name']
            properties_name = sku_dict['properties_name']
            arrival_quantity = inbound_sku_dict['arrival_quantity']
            inferior_quantity = inbound_sku_dict['inferior_quantity']
            district = inbound_sku_dict['district']
            m = self.DISTRICT_REGEX.match(district)
            if m:
                tmp = m.groupdict()
                pno = tmp.get('pno') or ''
                dno = tmp.get('dno') or ''
                deposite_district = DepositeDistrict.objects.get(
                    parent_no=pno,
                    district_no=dno)
                ProductLocation.objects.filter(product_id=product_id,
                                               sku_id=sku_id).delete()
                ProductLocation.objects.get_or_create(
                    product_id=product_id,
                    sku_id=sku_id,
                    district=deposite_district)

            inbound_sku_dict.update({
                'outer_id': outer_id,
                'product_name': product_name,
                'properties_name': properties_name
            })

            inbound_detail = inbound_details.get(sku_id)
            if inbound_detail:
                if inbound_detail.arrival_quantity == arrival_quantity and \
                                inbound_detail.inferior_quantity == inferior_quantity:
                    inbound_skus_dict.pop(sku_id, False)
                    continue
                else:
                    for record in inbound_detail.records.filter(
                            status=OrderDetailInBoundDetail.NORMAL):
                        if record.arrival_quantity:
                            record.orderdetail.arrival_quantity -= record.arrival_quantity
                            op_logs.append(self.ORDERDETAIL_OP_LOG_TPL %
                                           {'id': record.orderdetail.id,
                                            'msg':
                                                '到货数-%d' % record.arrival_quantity})
                        if record.inferior_quantity:
                            record.orderdetail.inferior_quantity -= record.inferior_quantity
                            op_logs.append(self.ORDERDETAIL_OP_LOG_TPL %
                                           {'id': record.orderdetail.id,
                                            'msg':
                                                '次品数-%d' % record.arrival_quantity})
                        orderlist_ids.add(record.orderdetail.orderlist_id)
                        record.orderdetail.save()

                        record.status = OrderDetailInBoundDetail.INVALID
                        record.save()
                        op_logs.append(self.ORDERDETAIL_INBOUNDDETAIL_OP_LOG_TPL
                                       % {'id': record.id,
                                          'msg': '设为无效'})
                    # 更新库存
                    arrival_quantity_delta = arrival_quantity - inbound_detail.arrival_quantity
                    if arrival_quantity_delta:
                        inbound_detail.sku.quantity += arrival_quantity_delta
                        inbound_detail.sku.save()
                        log_action(request.user.id, inbound_detail.sku, CHANGE,
                                   u'修改入仓单%d: 更新库存%+d' %
                                   (inbound.id, arrival_quantity_delta))

                    inbound_detail.arrival_quantity = arrival_quantity
                    inbound_detail.inferior_quantity = inferior_quantity
                    inbound_detail.save()
                    msg = '更新 到货数%d 次品数%d' % (arrival_quantity,
                                              inferior_quantity)
                    op_logs.append(self.INBOUNDDETAIL_OP_LOG_TPL %
                                   {'id': inbound_detail.id,
                                    'msg': msg})
                    log_action(request.user.id, inbound_detail, CHANGE, msg)
            else:
                inbound_detail = InBoundDetail(
                    inbound=inbound,
                    product_id=product_id,
                    sku_id=sku_id,
                    product_name=product_name,
                    outer_id=outer_id,
                    properties_name=properties_name,
                    arrival_quantity=arrival_quantity,
                    inferior_quantity=inferior_quantity)
                inbound_detail.save()
                op_logs.append(self.INBOUNDDETAIL_OP_LOG_TPL %
                               {'id': inbound_detail.id,
                                'msg': '创建 到货数%d 次品数%d' %
                                       (arrival_quantity, inferior_quantity)})
                inbound_details[sku_id] = inbound_detail

                if arrival_quantity > 0:
                    inbound_detail.sku.quantity += arrival_quantity
                    inbound_detail.sku.save()
                    log_action(request.user.id, inbound_detail.sku, CHANGE,
                               u'创建入仓单%d: 更新库存%+d' %
                               (inbound.id, arrival_quantity))

        for detail_dict in details:
            if not detail_dict.get('name'):
                continue
            detail_id = detail_dict['id']
            product_name = detail_dict.get('name') or ''
            properties_name = detail_dict.get('properties_name') or ''
            arrival_quantity = detail_dict.get('arrival_quantity') or 0
            inferior_quantity = detail_dict.get('inferior_quantity') or 0
            district = detail_dict.get('district') or ''
            if detail_id:
                inbound_detail = InBoundDetail.objects.get(id=detail_id)
                inbound_detail.product_name = product_name
                inbound_detail.properties_name = properties_name
                inbound_detail.arrival_quantity = arrival_quantity
                inbound_detail.inferior_quantity = inferior_quantity
                inbound_detail.district = district
                inbound_detail.save()
            else:
                inbound_detail = InBoundDetail(
                    inbound=inbound,
                    product_name=product_name,
                    properties_name=properties_name,
                    arrival_quantity=arrival_quantity,
                    inferior_quantity=inferior_quantity,
                    district=district)
                inbound_detail.save()
                detail_dict['id'] = inbound_detail.id

        orderlists_with_express_no = []
        orderlists_without_express_no = []
        for orderlist in OrderList.objects.filter(supplier_id=inbound.supplier_id) \
                .exclude(status__in=[OrderList.COMPLETED, OrderList.ZUOFEI]).order_by('created'):
            if form.cleaned_attrs.express_no and orderlist.express_no:
                if form.cleaned_attrs.express_no.strip() in \
                        self.EXPRESS_NO_SPLIT_PATTERN.split(orderlist.express_no.strip()):
                    orderlists_with_express_no.append(orderlist)
                    continue
            orderlists_without_express_no.append(orderlist)

        op_logs.append('重新分配入库单...')
        len_of_op_logs = len(op_logs)
        orderlists = orderlists_with_express_no + orderlists_without_express_no
        for orderlist in orderlists:
            for orderdetail in orderlist.order_list.all():
                sku_id = int(orderdetail.chichu_id)
                inbound_sku_dict = inbound_skus_dict.get(sku_id)
                inbound_detail = inbound_details.get(sku_id)
                if not (inbound_detail and inbound_sku_dict):
                    continue

                arrival_quantity_delta = max(
                    min(orderdetail.buy_quantity - orderdetail.arrival_quantity,
                        inbound_sku_dict['arrival_quantity']), 0)
                inferior_quantity_delta = max(
                    min(orderdetail.buy_quantity - orderdetail.arrival_quantity
                        - orderdetail.inferior_quantity,
                        inbound_sku_dict['inferior_quantity']), 0)

                if not (arrival_quantity_delta or inferior_quantity_delta):
                    continue
                orderlist_ids.add(orderlist.id)

                if arrival_quantity_delta > 0:
                    inbound_sku_dict[
                        'arrival_quantity'] -= arrival_quantity_delta
                    orderdetail.arrival_quantity += arrival_quantity_delta
                    orderdetail.save()
                    op_logs.append(self.ORDERDETAIL_OP_LOG_TPL %
                                   {'id': orderdetail.id,
                                    'msg':
                                        '更新 到货数+%d' % arrival_quantity_delta})

                if inferior_quantity_delta > 0:
                    inbound_sku_dict[
                        'inferior_quantity'] -= inferior_quantity_delta
                    orderdetail.inferior_quantity += inferior_quantity_delta
                    orderdetail.save()
                    op_logs.append(self.ORDERDETAIL_OP_LOG_TPL %
                                   {'id': orderdetail.id,
                                    'msg':
                                        '更新 次品数+%d' % inferior_quantity_delta})

                inbound_record = OrderDetailInBoundDetail(
                    orderdetail=orderdetail,
                    inbounddetail=inbound_detail,
                    arrival_quantity=arrival_quantity_delta,
                    inferior_quantity=inferior_quantity_delta)
                inbound_record.save()
                msg = '创建 订货明细ID:%d 入库明细ID:%d 到货数:+%d 次品数:+%d' % (
                    orderdetail.id, inbound_detail.id, arrival_quantity_delta,
                    inferior_quantity_delta)
                op_logs.append(self.ORDERDETAIL_INBOUNDDETAIL_OP_LOG_TPL %
                               {'id': inbound_record.id,
                                'msg': msg})
                if not (inbound_sku_dict.get('arrival_quantity') or
                            inbound_sku_dict.get('inferior_quantity')):
                    inbound_skus_dict.pop(sku_id, False)
        if len_of_op_logs == len(op_logs):
            op_logs.append('执行完毕, 无需重新分配')

        log_action(request.user.id, inbound, CHANGE, u'修改')
        self.update_orderlist(request, orderlist_ids, op_logs)
        self.update_inbound(request, inbound, inbound_skus_dict, op_logs)
        log_action(request.user.id, inbound, CHANGE,
                   mark_safe('\n'.join(op_logs)))
        return Response({'msg': ''.join(map(lambda x: '<p>%s</p>' % x, op_logs))
                         })

    @list_route(methods=['post'])
    def create_supplier_inbound(self, request):
        form = forms.EditInBoundForm(request.POST)
        if not form.is_valid():
            return Response({'error': '参数错误'})

        inbound_skus = json.loads(form.cleaned_attrs.skus)
        if not inbound_skus:
            return Response({'error': '请填写入库数据'})
        inbound_skus_dict = {int(x['sku_id']): x for x in inbound_skus}
        if not any([x['arrival_quantity'] + x['inferior_quantity']
                    for x in inbound_skus_dict.values()]):
            return Response({'error': '请填写入库数据'})
        details = json.loads(form.cleaned_attrs.details)

        supplier_id = form.cleaned_attrs.target_id
        old_skus_dict = {}
        dinghuo_stats = OrderDetail.objects.filter(orderlist__supplier_id=supplier_id) \
            .exclude(orderlist__status__in=[OrderList.COMPLETED, OrderList.ZUOFEI]) \
            .values('product_id', 'chichu_id') \
            .annotate(buy_quantity=Sum('buy_quantity'), arrival_quantity=Sum('arrival_quantity'),
                      inferior_quantity=Sum('inferior_quantity'))
        for s in dinghuo_stats:
            sku_id = int(s['chichu_id'])
            old_skus_dict[sku_id] = {
                'buy_quantity': s['buy_quantity'],
                'arrival_quantity': s['arrival_quantity'],
                'inferior_quantity': s['inferior_quantity'],
                'plan_quantity': s['buy_quantity'] - min(
                    s['arrival_quantity'],
                    s['buy_quantity']) - s['inferior_quantity']
            }

        inbound = InBound(supplier_id=supplier_id,
                          sent_from=InBound.SUPPLIER,
                          creator=request.user,
                          images=json.loads(form.cleaned_attrs.images or '[]'),
                          memo=form.cleaned_attrs.memo)
        if form.cleaned_attrs.express_no:
            inbound.express_no = form.cleaned_attrs.express_no
        inbound.save()

        skus_dict = {}
        for sku in ProductSku.objects.select_related('product').filter(
                id__in=inbound_skus_dict.keys()):
            skus_dict[sku.id] = {
                'product_id': sku.product.id,
                'sku_id': sku.id,
                'outer_id': sku.product.outer_id,
                'product_name': sku.product.name,
                'properties_name': sku.properties_name or
                                   sku.properties_alias or '',
                'quantity': sku.quantity
            }

        inbound_details = {}
        for sku_id, inbound_sku_dict in inbound_skus_dict.iteritems():
            sku_dict = skus_dict.get(sku_id)
            if not sku_dict:
                continue
            product_id = sku_dict['product_id']
            outer_id = sku_dict['outer_id']
            product_name = sku_dict['product_name']
            properties_name = sku_dict['properties_name']
            arrival_quantity = inbound_sku_dict['arrival_quantity']
            inferior_quantity = inbound_sku_dict['inferior_quantity']
            district = inbound_sku_dict.get('district') or ''

            inbound_sku_dict.update({
                'outer_id': outer_id,
                'product_name': product_name,
                'properties_name': properties_name
            })

            m = self.DISTRICT_REGEX.match(district)
            if m:
                tmp = m.groupdict()
                pno = tmp.get('pno') or ''
                dno = tmp.get('dno') or ''
                deposite_district = DepositeDistrict.objects.get(
                    parent_no=pno,
                    district_no=dno)
                ProductLocation.objects.get_or_create(
                    product_id=product_id,
                    sku_id=sku_id,
                    district=deposite_district)

            inbound_detail = InBoundDetail(inbound=inbound,
                                           product_id=product_id,
                                           sku_id=sku_id,
                                           product_name=product_name,
                                           outer_id=outer_id,
                                           properties_name=properties_name,
                                           arrival_quantity=arrival_quantity,
                                           inferior_quantity=inferior_quantity)
            inbound_detail.save()
            inbound_details[sku_id] = inbound_detail

            # 更新库存
            if arrival_quantity > 0:
                inbound_detail.sku.quantity += arrival_quantity
                inbound_detail.sku.save()
                log_action(request.user.id, inbound_detail.sku, CHANGE,
                           u'创建入仓单%d: 更新库存%+d' % (inbound.id, arrival_quantity))

        for detail_dict in details:
            if detail_dict['id']:
                continue
            if not detail_dict.get('name'):
                continue
            product_name = detail_dict['name']
            properties_name = detail_dict.get('properties_name') or ''
            arrival_quantity = detail_dict.get('arrival_quantity') or 0
            inferior_quantity = detail_dict.get('inferior_quantity') or 0
            district = detail_dict.get('district') or ''

            inbound_detail = InBoundDetail(inbound=inbound,
                                           product_name=product_name,
                                           properties_name=properties_name,
                                           arrival_quantity=arrival_quantity,
                                           inferior_quantity=inferior_quantity,
                                           district=district)
            inbound_detail.save()
            detail_dict['id'] = inbound_detail.id

        orderlists_with_express_no = []
        orderlists_without_express_no = []
        for orderlist in OrderList.objects.filter(supplier_id=form.cleaned_attrs.target_id) \
                .exclude(status__in=[OrderList.COMPLETED, OrderList.ZUOFEI]).order_by('created'):
            if form.cleaned_attrs.express_no and orderlist.express_no:
                if form.cleaned_attrs.express_no.strip() in \
                        self.EXPRESS_NO_SPLIT_PATTERN.split(orderlist.express_no.strip()):
                    orderlists_with_express_no.append(orderlist)
                    continue
            orderlists_without_express_no.append(orderlist)

        op_logs = []
        orderlist_ids = set()
        orderlists = orderlists_with_express_no + orderlists_without_express_no
        for orderlist in orderlists:
            for orderdetail in orderlist.order_list.all():
                sku_id = int(orderdetail.chichu_id)
                inbound_sku_dict = inbound_skus_dict.get(sku_id)
                inbound_detail = inbound_details.get(sku_id)
                if not (inbound_detail and inbound_sku_dict):
                    continue

                arrival_quantity_delta = max(
                    min(orderdetail.buy_quantity - orderdetail.arrival_quantity,
                        inbound_sku_dict['arrival_quantity']), 0)
                inferior_quantity_delta = max(
                    min(orderdetail.buy_quantity - orderdetail.arrival_quantity
                        - orderdetail.inferior_quantity,
                        inbound_sku_dict['inferior_quantity']), 0)

                if not (arrival_quantity_delta or inferior_quantity_delta):
                    continue
                orderlist_ids.add(orderlist.id)

                if arrival_quantity_delta > 0:
                    inbound_sku_dict[
                        'arrival_quantity'] -= arrival_quantity_delta
                    orderdetail.arrival_quantity += arrival_quantity_delta
                    orderdetail.save()
                    op_logs.append(self.ORDERDETAIL_OP_LOG_TPL %
                                   {'id': orderdetail.id,
                                    'msg':
                                        '到货数+%d' % orderdetail.arrival_quantity})

                if inferior_quantity_delta > 0:
                    inbound_sku_dict[
                        'inferior_quantity'] -= inferior_quantity_delta
                    orderdetail.inferior_quantity += inferior_quantity_delta
                    orderdetail.save()
                    op_logs.append(self.ORDERDETAIL_OP_LOG_TPL %
                                   {'id': orderdetail.id,
                                    'msg':
                                        '次品数+%d' % orderdetail.inferior_quantity})

                inbound_record = OrderDetailInBoundDetail(
                    orderdetail=orderdetail,
                    inbounddetail=inbound_detail,
                    arrival_quantity=arrival_quantity_delta,
                    inferior_quantity=inferior_quantity_delta)
                inbound_record.save()
                msg = '创建 订货明细ID:%d 入库明细ID:%d 到货数:+%d 次品数:+%d' % (
                    orderdetail.id, inbound_detail.id, arrival_quantity_delta,
                    inferior_quantity_delta)
                op_logs.append(self.ORDERDETAIL_INBOUNDDETAIL_OP_LOG_TPL %
                               {'id': inbound_record.id,
                                'msg': msg})

                if not (inbound_sku_dict.get('arrival_quantity') or
                            inbound_sku_dict.get('inferior_quantity')):
                    inbound_skus_dict.pop(sku_id, False)

        log_action(request.user.id, inbound, ADDITION, u'新建')
        self.update_orderlist(request, orderlist_ids, op_logs)
        self.update_inbound(request, inbound, inbound_skus_dict, op_logs)
        log_action(request.user.id, inbound, CHANGE,
                   mark_safe('\n'.join(op_logs)))
        return Response({'inbound_id': inbound.id,
                         'msg': ''.join(map(lambda x: '<p>%s</p>' % x,
                                            op_logs)),
                         'details': details})

    @list_route(methods=['get'])
    def list_for_inbound(self, request):
        data = []
        error = None

        def _refund_data(refund_id):
            pass

        def _inbound_data(inbound_id):
            details = []
            products_dict = {}
            sku_ids = set()
            inbound = InBound.objects.get(id=inbound_id)
            for inbound_detail in InBoundDetail.objects.filter(
                    inbound=inbound).order_by('id'):
                if not inbound_detail.sku:
                    details.append({
                        'id': inbound_detail.id,
                        'name': inbound_detail.product_name or '',
                        'properties_name': inbound_detail.properties_name,
                        'arrival_quantity': inbound_detail.arrival_quantity or
                                            0,
                        'inferior_quantity': inbound_detail.inferior_quantity or
                                             0,
                        'district': inbound_detail.district
                    })
                else:
                    sku_ids.add(inbound_detail.sku_id)
                    skus_dict = products_dict.setdefault(
                        inbound_detail.product_id, {})
                    s = inbound_detail.records.filter(status=OrderDetailInBoundDetail.NORMAL) \
                        .values('inbounddetail_id').annotate(arrival_quantity=Sum('arrival_quantity'),
                                                             inferior_quantity=Sum('inferior_quantity'))
                    s = {} if not s else s[0]
                    skus_dict[inbound_detail.sku_id] = {
                        'id': inbound_detail.sku_id,
                        'arrival_quantity': inbound_detail.arrival_quantity,
                        'inferior_quantity': inbound_detail.inferior_quantity,
                        'plan_quantity': s.get('arrival_quantity') or 0
                    }

            dinghuo_stats = OrderDetail.objects.filter(chichu_id__in=map(str, skus_dict.keys())) \
                .exclude(orderlist__status__in=[OrderList.COMPLETED, OrderList.ZUOFEI]) \
                .values('product_id', 'chichu_id') \
                .annotate(buy_quantity=Sum('buy_quantity'), arrival_quantity=Sum('arrival_quantity'),
                          inferior_quantity=Sum('inferior_quantity'))
            for s in dinghuo_stats:
                product_id, sku_id = map(int, (s['product_id'], s['chichu_id']))
                skus_dict = products_dict.setdefault(product_id, {})
                sku_dict = skus_dict[sku_id]
                sku_dict.update({
                    'id': sku_id,
                    'plan_quantity': s['buy_quantity'] - s[
                        'arrival_quantity'] + sku_dict['plan_quantity']
                })
            new_products_dict = {}
            for sku in ProductSku.objects.select_related('product').filter(
                    id__in=list(sku_ids)):
                product_id = sku.product.id
                sku_id = sku.id

                product_location = None
                product_locations = ProductLocation.objects.select_related(
                    'district').filter(product_id=product_id,
                                       sku_id=sku_id)[:1]
                if product_locations:
                    product_location = product_locations[0]
                product_dict = new_products_dict.setdefault(product_id, {
                    'id': product_id,
                    'name': sku.product.name,
                    'outer_id': sku.product.outer_id,
                    'pic_path': '%s' % sku.product.pic_path.strip(),
                    'ware_by': sku.product.ware_by,
                    'skus': {}
                })
                sku_dict = products_dict[product_id][sku_id]
                sku_dict.update({
                    'properties_name': sku.properties_name or
                                       sku.properties_alias,
                    'quantity': sku.quantity,
                    'barcode': sku.barcode
                })
                if product_location:
                    sku_dict['district'] = str(product_location.district)
                product_dict['skus'][sku_id] = sku_dict

            products = []
            for product_id in sorted(new_products_dict.keys()):
                product_dict = new_products_dict[product_id]
                product_dict['skus'] = [
                    product_dict['skus'][k]
                    for k in sorted(product_dict['skus'].keys())
                    ]
                products.append(product_dict)
            return products, details, inbound

        def _supplier_data(supplier_id):
            sku_ids = set()
            products_dict = {}

            dinghuo_stats = OrderDetail.objects.filter(orderlist__supplier_id=supplier_id) \
                .exclude(orderlist__status__in=[OrderList.COMPLETED, OrderList.ZUOFEI]) \
                .values('product_id', 'chichu_id') \
                .annotate(buy_quantity=Sum('buy_quantity'), arrival_quantity=Sum('arrival_quantity'),
                          inferior_quantity=Sum('inferior_quantity'))
            for s in dinghuo_stats:
                product_id, sku_id = map(int, (s['product_id'], s['chichu_id']))
                sku_ids.add(sku_id)

                plan_quantity = s['buy_quantity'] - s['arrival_quantity']
                if plan_quantity <= 0:
                    continue
                skus_dict = products_dict.setdefault(product_id, {})
                skus_dict[sku_id] = {
                    'id': sku_id,
                    'plan_quantity': plan_quantity
                }

            saleproduct_ids = set()
            new_products_dict = {}
            for sku in ProductSku.objects.select_related('product').filter(
                    id__in=list(sku_ids)):
                product_id = sku.product.id
                sku_id = sku.id
                if not (product_id in products_dict and
                                sku_id in products_dict[product_id]):
                    continue
                saleproduct_ids.add(sku.product.sale_product)
                product_location = None
                product_locations = ProductLocation.objects.select_related(
                    'district').filter(product_id=product_id,
                                       sku_id=sku_id)[:1]
                if product_locations:
                    product_location = product_locations[0]

                product_dict = new_products_dict.setdefault(
                    product_id,
                    {'id': product_id,
                     'saleproduct_id': sku.product.sale_product,
                     'name': sku.product.name,
                     'outer_id': sku.product.outer_id,
                     'pic_path': '%s' % sku.product.pic_path.strip(),
                     'ware_by': sku.product.ware_by,
                     'skus': {}})

                sku_dict = products_dict[product_id][sku_id]
                sku_dict.update({
                    'properties_name': sku.properties_name or
                                       sku.properties_alias,
                    'quantity': sku.quantity,
                    'barcode': sku.barcode
                })
                if product_location:
                    sku_dict['district'] = str(product_location.district)
                product_dict['skus'][sku_id] = sku_dict

            saleproducts_dict = {}
            for saleproduct in SaleProduct.objects.filter(
                    id__in=list(saleproduct_ids)):
                saleproducts_dict[saleproduct.id] = saleproduct.product_link

            data = []
            for product_id in sorted(new_products_dict.keys()):
                product_dict = new_products_dict[product_id]
                product_dict['product_link'] = saleproducts_dict.get(
                    product_dict['saleproduct_id']) or '#'
                product_dict['skus'] = [
                    product_dict['skus'][k]
                    for k in sorted(product_dict['skus'].keys())
                    ]
                data.append(product_dict)
            return data

        supplier_dict = {}
        express_no_dict = {}
        for orderlist in OrderList.objects.select_related('supplier').exclude(
                status__in=[OrderList.COMPLETED, OrderList.ZUOFEI,
                            OrderList.CLOSED, OrderList.TO_PAY]):
            if not orderlist.supplier_id:
                continue
            if orderlist.supplier_id not in supplier_dict:
                supplier_dict[
                    orderlist.supplier_id] = orderlist.supplier.supplier_name
            if orderlist.express_no:
                for express_no in self.EXPRESS_NO_SPLIT_PATTERN.split(
                        orderlist.express_no.strip()):
                    express_no_dict[express_no.strip()] = orderlist.supplier_id

        result = {
            'suppliers': [{'id': k,
                           'text': '%s(%d)' % (supplier_dict[k], k)}
                          for k in sorted(supplier_dict.keys())],
            'express_nos': [{'id': express_no_dict[k],
                             'text': k,
                             'sent_from': InBound.SUPPLIER}
                            for k in sorted(express_no_dict.keys())],
            'ware_choices': [{'value': v,
                              'text': t} for v, t in WARE_CHOICES]
        }
        form = forms.EditInBoundForm(request.GET)
        if not form.is_valid():
            error = '输入有错误'
        else:
            result.update(form.json)
            if form.cleaned_attrs.inbound_id:
                products, details, inbound = _inbound_data(
                    form.cleaned_attrs.inbound_id)
                result.update({
                    'products': products,
                    'details': details,
                    'images': inbound.images or [],
                    'memo': inbound.memo or '',
                    'target_id': inbound.supplier.id,
                    'supplier_name': inbound.supplier.supplier_name
                })
            else:
                if form.cleaned_attrs.sent_from == InBound.SUPPLIER:
                    supplier_id = None
                    if form.cleaned_attrs.target_id:
                        supplier_id = form.cleaned_attrs.target_id
                    else:
                        if form.cleaned_attrs.supplier:
                            for sid, supplier_name in supplier_dict.iteritems():
                                if supplier_name.strip(
                                ) == form.cleaned_attrs.supplier:
                                    supplier_id = sid
                                    break
                    if not supplier_id:
                        error = '找不到供应商'
                    else:
                        result['products'] = _supplier_data(supplier_id)
                        result['supplier_name'] = supplier_dict[supplier_id]
                elif form.sent_from == InBound.REFUND:
                    pass
        return Response(result, template_name='dinghuo/inbound.html')

    @detail_route(methods=['get'])
    def get_sku_inbound_detail(self, request, pk):
        sku_id = request.REQUEST.get('sku_id', None)
        orderlist = get_object_or_404(OrderList, id=pk)
        sku = get_object_or_404(ProductSku, id=sku_id)
        ois = OrderDetailInBoundDetail.objects.filter(orderdetail__orderlist_id=pk, inbounddetail__sku_id=sku.id,
                                                      inbounddetail__checked=True). \
            select_related('orderdetail', 'inbounddetail').distinct()
        res = []
        for oi in ois:
            item = {
                'inbound_id': oi.inbounddetail.inbound_id,
                'arrival_quantity': oi.inbounddetail.arrival_quantity,
                'inferior_quantity': oi.inbounddetail.inferior_quantity,
                'allocate_quantity': oi.arrival_quantity
            }
            res.append(item)
        return Response({'res': res}, template_name=u"dinghuo/order_sku_inbound_detail.htm")

    @detail_route(methods=['get'])
    def get_sku_inferior_detail(self, request, pk):
        sku_id = request.REQUEST.get('sku_id', None)
        orderlist = get_object_or_404(OrderList, id=pk)
        sku = get_object_or_404(ProductSku, id=sku_id)
        ois = OrderDetailInBoundDetail.objects.filter(inbounddetail__sku_id=sku.id, inbounddetail__checked=True,
                                                      inferior_quantity__gt=0). \
            select_related('orderdetail', 'inbounddetail').distinct()
        res = []
        for oi in ois:
            item = {
                'inbound_id': oi.inbounddetail.inbound_id,
                'inferior_quantity': oi.inbounddetail.inferior_quantity,
                'inbound_time': oi.inbounddetail.inbound.created.strftime("%Y-%m-%d %H")
            }
            res.append(item)
        already_return = RGDetail.get_inferior_total(sku_id)
        return Response({'res': res, 'already_return': already_return},
                        template_name=u"dinghuo/order_sku_inferior_detail.htm")

    @detail_route(methods=['get'])
    def export_package(self, request, pk):
        orderlist = get_object_or_404(OrderList, pk=pk)
        columns = [u'订单号', u'产品条码', u'订单状态', u'买家id', u'子订单编号', u'供应商编码', u'买家昵称', u'商品名称', u'产品规格', u'商品单价', u'商品数量',
                   u'商品总价', u'运费', u'购买优惠信息', u'总金额', u'买家购买附言', u'收货人姓名', u'收货地址', u'邮编',
                   u'收货人手机', u'收货人电话', u'买家选择运送方式', u'卖家备忘内容', u'订单创建时间', u'付款时间', u'物流公司', u'物流单号', u'发货附言',
                   u'发票抬头', u'电子邮件', u'商品链接']

        need_send = PackageSkuItem.objects.filter(purchase_order_unikey=orderlist.purchase_order_unikey)
        need_send_ids = [n.id for n in need_send]
        items = [columns]
        if orderlist.third_package:
            if PackageSkuItem.objects.filter(purchase_order_unikey=orderlist.purchase_order_unikey,
                                         assign_status=0).exists():
                raise exceptions.ValidationError(make_response(u'此订货单下存在未分配的包裹'))
            export_condition = {
                'id__in': need_send_ids
            }
            package_order_ids = list(set(
                [p.package_order_pid for p in PackageSkuItem.objects.filter(**export_condition)]))
            for o in PackageOrder.objects.filter(pid__in=package_order_ids):
                for p in o.package_sku_items.filter(**export_condition):
                    saleproduct = p.product_sku.product.get_sale_product()
                    items.append([str(o.pid), '', o.sys_status, str(o.buyer_id), str(p.id), saleproduct.supplier_sku if saleproduct else '', str(o.buyer_nick),
                                str(p.product_sku.product.name), str(p.product_sku.properties_name),
                                str(p.product_sku.product.cost), str(p.num), '0', '0', '0', '0', '', str(o.receiver_name),
                                str(o.receiver_address_detail), '', o.receiver_mobile, '', '', '', '',
                                p.sale_trade.created.strftime('%Y-%m-%D %H:%M:%S'), p.sale_trade.pay_time.strftime('%Y-%m-%D %H:%M:%S'),
                                p.sale_trade.logistics_company.name if p.sale_trade.logistics_company else '', '', u'小鹿美美，时尚健康美丽', '', '',saleproduct.product_link if saleproduct else ''])
        else:
            for p in need_send:
                o = p.package_order
                saleproduct = p.product_sku.product.get_sale_product()
                items.append([str(o.pid) if o else '', '', p.get_assign_status_display(), p.sale_trade.buyer_id, str(p.id), saleproduct.supplier_sku if saleproduct else '', str(p.sale_trade.buyer_nick),
                            str(p.product_sku.product.name), str(p.product_sku.properties_name),
                            str(p.product_sku.product.cost), str(p.num), '0', '0', '0', '0', '', str(o.receiver_name),
                            str(p.sale_trade.receiver_address_detail), '', p.sale_trade.receiver_mobile, '', '', '', '',
                            p.sale_trade.created.strftime('%Y-%m-%D %H:%M:%S'), p.sale_trade.pay_time.strftime('%Y-%m-%D %H:%M:%S'),
                            p.sale_trade.logistics_company.name if p.sale_trade.logistics_company else '', '', u'小鹿美美，时尚健康美丽', '', '',saleproduct.product_link if saleproduct else ''])

        buff = StringIO()
        is_windows = request.META['HTTP_USER_AGENT'].lower().find(
            'windows') > -1
        writer = CSVUnicodeWriter(buff,
                                  encoding=is_windows and 'gbk' or 'utf-8')
        writer.writerows(items)
        response = HttpResponse(buff.getvalue(),
                                content_type='application/octet-stream')
        response[
            'Content-Disposition'] = 'attachment;filename=packagedetail-%s.csv' % orderlist.id
        return response

    @detail_route(methods=['POST'])
    def import_package(self, request, pk):
        data = request.DATA.get('data')
        print data
        order_list = get_object_or_404(OrderList, pk=pk)
        errors = []
        for item in data:
            try:
                out_sid = item.get(u'物流单号')
                logistics_company_id = item.get(u'物流公司id')
                pid = item.get(u'包裹单号')
                package_order = PackageOrder.objects.get(pid=pid)
                if not package_order.package_sku_items.filter(purchase_order_unikey=order_list.purchase_order_unikey):
                    errors.append(u'订货单中%d不存在这个包裹:%s-%s' % (order_list.id, pid, out_sid))
                    continue
                if package_order.sys_status not in [PackageOrder.WAIT_CUSTOMER_RECEIVE, PackageOrder.FINISHED_STATUS]:
                    package_order.out_sid = out_sid
                    logistics_company = LogisticsCompany.objects.get(id=logistics_company_id)
                    package_order.finish_third_package(out_sid, logistics_company)
            except Exception, e0:
                errors.append(e0.message)
        order_list.set_by_package_sku_item()
        if errors:
            return Response(make_response(info=str(len(errors)) + '个导入错误。错误信息：'+','.join([str(e) for e in errors])))
        return Response(SUCCESS_RESPONSE)

    @detail_route(methods=['POST'])
    def reduce_sku_num(self, request, pk):
        order_list = get_object_or_404(OrderList, id=pk)
        try:
            sku_id = int(request.get('sku_id', 0))
            num = int(request.get('num', 0))
        except Exception, e0:
            raise exceptions.ValidationError(e0.message)
        try:
            order_list.reduce_sku_num(sku_id, num)
        except Exception, e0:
            raise exceptions.ValidationError(e0.message)
        return Response(SUCCESS_RESPONSE)