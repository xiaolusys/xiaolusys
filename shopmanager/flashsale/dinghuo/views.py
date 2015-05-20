# coding:utf-8

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render
from django.core import serializers
from shopback.items.models import Product, ProductSku
from flashsale.dinghuo.models import orderdraft, OrderDetail, OrderList
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
import json, datetime
from django.views.decorators.csrf import csrf_exempt
from flashsale.dinghuo import paramconfig as pcfg
from django.template import RequestContext
from django.core.paginator import Paginator, InvalidPage, EmptyPage, PageNotAnInteger
from flashsale.dinghuo import log_action, ADDITION, CHANGE
from django.db.models import F
from django.views.generic import View
from django.contrib.auth.models import User


def orderadd(request):
    user = request.user
    orderDr = orderdraft.objects.all().filter(buyer_name=user)

    return render_to_response('dinghuo/orderadd.html', {"orderdraft": orderDr},
                              context_instance=RequestContext(request))


def searchProduct(request):
    response = HttpResponse()
    response['Content-Type'] = "text/javascript"
    ProductIDFrompage = request.GET.get("searchtext", "")
    productRestult = Product.objects.filter(outer_id__icontains=ProductIDFrompage)
    # data = serializers.serialize("json", productRestult)
    product_list = []
    for product in productRestult:
        product_dict = model_to_dict(product)
        product_dict['prod_skus'] = []

        guiges = product.prod_skus.all()
        for guige in guiges:
            sku_dict = model_to_dict(guige)
            product_dict['prod_skus'].append(sku_dict)

        product_list.append(product_dict)

    data = json.dumps(product_list, cls=DjangoJSONEncoder)
    return HttpResponse(data)


@csrf_exempt
def initdraft(request):
    user = request.user
    if request.method == "POST":

        post = request.POST

        product_counter = int(post["product_counter"])
        for i in range(1, product_counter + 1):
            product_id_index = "product_id_" + str(i)
            product_id = post[product_id_index]
            guiges = ProductSku.objects.filter(product_id=product_id)
            for guige in guiges:
                guigequantityindex = product_id + "_tb_quantity_" + str(guige.id)
                guigequantity = post[guigequantityindex]
                mairujiageindex = product_id + "_tb_cost_" + str(guige.id)
                mairujiage = post[mairujiageindex]
                mairujiage = float(mairujiage)
                if guigequantity and mairujiage and mairujiage != 0 and guigequantity != "0":
                    guigequantity = int(guigequantity)
                    mairujiage = float(mairujiage)
                    try:
                        p1 = Product.objects.get(id=product_id)
                    except Exception as e:
                        print e
                    draftquery = orderdraft.objects.filter(buyer_name=user, product_id=product_id,
                                                           chichu_id=guige.id)
                    if draftquery:
                        draftquery[0].buy_quantity = draftquery[0].buy_quantity + guigequantity
                        draftquery[0].save()
                    else:
                        shijian = datetime.datetime.now()
                        tdraft = orderdraft(buyer_name=user, product_id=product_id, outer_id=p1.outer_id,
                                            buy_quantity=guigequantity, product_name=p1.name, buy_unitprice=mairujiage,
                                            chichu_id=guige.id, product_chicun=guige.name, created=shijian)
                        tdraft.save()
                else:
                    guigequantity = 0
        return HttpResponseRedirect("/sale/dinghuo/dingdan/")
    elif request.method == "GET":
        response = HttpResponse()
        response['Content-Type'] = "text/javascript"
        tb_id = request.GET.get("tb_outer", "hello")
        tb_outer_id = request.GET.get("tb_outer_id", "")
        buy_quantity = request.GET.get("buy_quantity", "0")

        tb_sku_name = request.GET.get("tb_sku_name", "")
        buy_unitprice = request.GET.get("but_unit_price", "")
        try:
            productRestult = Product.objects.get(outer_id=tb_outer_id)
        except Exception as e:
            print e
        draftqueryset = orderdraft.objects.filter(product_id=tb_outer_id, product_chicun=tb_sku_name)
        if draftqueryset:
            draftqueryset[0].buy_quantity = draftqueryset[0].buy_quantity + int(buy_quantity)
            draftqueryset[0].save()
        else:
            try:
                shijian = datetime.datetime.now()
                oDraft = orderdraft(buyer_name=user, product_id=tb_outer_id, buy_quantity=int(buy_quantity),
                                    product_name=productRestult.name, buy_unitprice=float(buy_unitprice), chichu_id="1",
                                    product_chicun=tb_sku_name, created=shijian)

                oDraft.save()
            except Exception as e:
                print e
        orderDrAll = orderdraft.objects.all().filter(buyer_name=user)
        data = serializers.serialize("json", orderDrAll)
        return HttpResponse(data)


@csrf_exempt
def neworder(request):
    username = request.user
    orderDrAll = orderdraft.objects.all().filter(buyer_name=username)
    orderlist = None
    if request.method == 'POST':
        post = request.POST
        costofems = post['costofems']
        if costofems == "":
            costofems = 0
        else:
            costofems = float(costofems)
        shijian = datetime.datetime.now()
        receiver = post['consigneeName']
        supplierId = post['supplierId']
        storehouseId = post['storehouseId']
        express_company = post['express_company']
        express_no = post['express_no']
        businessDate = datetime.datetime.now()
        remarks = post['remarks']
        amount = calamount(username, costofems)
        orderlist = OrderList()
        orderlist.buyer_name = username
        orderlist.costofems = costofems*100
        orderlist.receiver = receiver
        orderlist.express_company = express_company
        orderlist.express_no = express_no
        orderlist.supplier_name = supplierId
        orderlist.created = businessDate
        orderlist.updated = businessDate
        orderlist.note = remarks
        orderlist.status = pcfg.SUBMITTING
        orderlist.order_amount = amount
        orderlist.save()

        drafts = orderdraft.objects.filter(buyer_name=username)
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
            orderdetail1.created = shijian
            orderdetail1.updated = shijian
            orderdetail1.save()
        drafts.delete()
        log_action(request.user.id, orderlist, CHANGE, u'新建订货单')
        return HttpResponseRedirect("/sale/dinghuo/detail/" + str(orderlist.id))

    return render_to_response('dinghuo/shengchengorder.html', {"orderdraft": orderDrAll},
                              context_instance=RequestContext(request))


def calamount(u, costofems):
    amount = 0;
    drafts = orderdraft.objects.all().filter(buyer_name=u)
    try:
        for draft in drafts:
            amount = amount + draft.buy_unitprice * draft.buy_quantity
        amount = amount + costofems
    except Exception as e:
        print e
    return amount


def CheckOrderExist(request):
    response = HttpResponse()
    response['Content-Type'] = "text/javascript"
    orderIDFrompage = request.GET.get("orderID", "")
    orderM = OrderList.objects.filter(id=orderIDFrompage)
    if orderM:
        result = """{"result":true}"""
    else:
        result = """{"result":false}"""
    return HttpResponse(result)


def delcaogao(request):
    username = request.user
    drafts = orderdraft.objects.filter(buyer_name=username)
    drafts.delete()
    return HttpResponse("")


def addpurchase(request):
    user = request.user
    ProductIDFrompage = "10802";
    productRestult = Product.objects.filter(outer_id__icontains=ProductIDFrompage)
    productguige = ProductSku.objects.all()
    orderDrAll = orderdraft.objects.all().filter(buyer_name=user)
    return render_to_response("dinghuo/addpurchasedetail.html",
                              {"productRestult": productRestult,
                               "productguige": productguige,
                               "drafts": orderDrAll},
                              context_instance=RequestContext(request))


def test(req):
    return render_to_response("dinghuo/testJsonto.html")


@csrf_exempt
def plusquantity(req):
    post = req.POST
    draftid = post["draftid"]
    draft = orderdraft.objects.get(id=draftid)
    draft.buy_quantity = draft.buy_quantity + 1
    draft.save()
    return HttpResponse("OK")


@csrf_exempt
def plusordertail(req):
    post = req.POST
    orderdetailid = post["orderdetailid"]
    orderdetail = OrderDetail.objects.get(id=orderdetailid)
    orderlist = OrderList.objects.get(id=orderdetail.orderlist_id)
    OrderDetail.objects.filter(id=orderdetailid).update(buy_quantity=F('buy_quantity') + 1)
    OrderDetail.objects.filter(id=orderdetailid).update(total_price=F('total_price') + orderdetail.buy_unitprice)
    OrderList.objects.filter(id=orderdetail.orderlist_id).update(
        order_amount=F('order_amount') + orderdetail.buy_unitprice)
    log_action(req.user.id, orderlist, CHANGE, u'订货单{0}{1}'.format((u'加一件'), orderdetail.product_name))
    log_action(req.user.id, orderdetail, CHANGE, u'%s' % (u'加一'))
    return HttpResponse("OK")


@csrf_exempt
def minusquantity(req):
    post = req.POST
    draftid = post["draftid"]
    draft = orderdraft.objects.get(id=draftid)
    draft.buy_quantity = draft.buy_quantity - 1
    draft.save()
    return HttpResponse("OK")


@csrf_exempt
def minusordertail(req):
    post = req.POST
    orderdetailid = post["orderdetailid"]
    orderdetail = OrderDetail.objects.get(id=orderdetailid)
    orderlist = OrderList.objects.get(id=orderdetail.orderlist_id)
    OrderDetail.objects.filter(id=orderdetailid).update(buy_quantity=F('buy_quantity') - 1)
    OrderDetail.objects.filter(id=orderdetailid).update(total_price=F('total_price') - orderdetail.buy_unitprice)
    orderdetail = OrderDetail.objects.get(id=orderdetailid)
    OrderList.objects.filter(id=orderdetail.orderlist_id).update(
        order_amount=F('order_amount') - orderdetail.buy_unitprice)
    log_action(req.user.id, orderlist, CHANGE, u'订货单{0}{1}'.format((u'加一件'), orderdetail.product_name))
    log_action(req.user.id, orderdetail, CHANGE, u'%s' % (u'减一'))
    return HttpResponse("OK")


@csrf_exempt
def removedraft(req):
    post = req.POST
    draftid = post["draftid"]
    draft = orderdraft.objects.get(id=draftid)
    draft.delete()
    return HttpResponse("OK")


@csrf_exempt
def viewdetail(req, orderdetail_id):
    orderlist = OrderList.objects.get(id=orderdetail_id)
    orderdetail = OrderDetail.objects.filter(orderlist_id=orderdetail_id)
    return render_to_response("dinghuo/orderdetail.html", {"orderlist": orderlist,
                                                           "orderdetails": orderdetail},
                              context_instance=RequestContext(req))


@csrf_exempt
def detaillayer(req, orderdetail_id):
    orderlist = OrderList.objects.get(id=orderdetail_id)
    orderdetail = OrderDetail.objects.filter(orderlist_id=orderdetail_id)
    return render_to_response("dinghuo/layerdetail.html", {"orderlist": orderlist,
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
    log_action(req.user.id, orderlist, CHANGE, u'%s采购单' % (state and u'审核' or u'作废'))
    return HttpResponse("OK")


@csrf_exempt
def changedetail(req, orderdetail_id):
    orderlist = OrderList.objects.get(id=orderdetail_id)
    orderdetail = OrderDetail.objects.filter(orderlist_id=orderdetail_id)
    return render_to_response("dinghuo/changedetail.html", {"orderlist": orderlist,
                                                            "orderdetails": orderdetail},
                              context_instance=RequestContext(req))


from shopback.items.models import Product


class dailystatsview(View):
    def getUserName(self, uid):
        try:
            return User.objects.get(pk=uid).username
        except:
            return 'none'

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

        time_from = datetime.datetime(target_date.year, target_date.month, target_date.day)
        time_to = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)

        prev_day = target_date - datetime.timedelta(days=1)
        next_day = None
        if target_date < today:
            next_day = target_date + datetime.timedelta(days=1)

        orderlists = OrderList.objects.exclude(status=u'作废').filter(created=target_date)
        orderlists_list = []
        for orderlist in orderlists:
            orderlist_dict = model_to_dict(orderlist)
            orderlist_dict['orderdetail'] = []

            orderdetails = OrderDetail.objects.filter(orderlist_id=orderlist.id)
            list = []
            for orderdetail in orderdetails:
                orderdetailouter_id = orderdetail.outer_id
                searchouterid = orderdetailouter_id[0: len(str(orderdetailouter_id)) - 1]
                list.append(searchouterid)
            list = {}.fromkeys(list).keys()

            for listbean in list:
                temporder = orderdetails.filter(outer_id__icontains=listbean)
                tempproduct = Product.objects.filter(outer_id__icontains=listbean)
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

            orderlists_list.append(orderlist_dict)

        return render_to_response("dinghuo/dailystats.html",
                                  {"orderlists_lists": orderlists_list, "prev_day": prev_day,
                                   "target_date": target_date, "next_day": next_day},
                                  context_instance=RequestContext(request))
