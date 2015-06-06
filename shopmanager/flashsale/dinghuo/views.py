# coding:utf-8

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core import serializers
from shopback.items.models import Product, ProductSku
from flashsale.dinghuo.models import orderdraft, OrderDetail, OrderList
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
import json, datetime
from django.views.decorators.csrf import csrf_exempt
from flashsale.dinghuo import paramconfig as pcfg
from django.template import RequestContext
from flashsale.dinghuo import log_action, CHANGE
from django.db.models import F, Q, Sum
from django.views.generic import View
from django.contrib.auth.models import User
import functions


def search_product(request):
    response = HttpResponse()
    response['Content-Type'] = "text/javascript"
    product_id_from_page = request.GET.get("searchtext", "")
    product_id_from_page = product_id_from_page.strip()
    product_result = Product.objects.filter(
        Q(outer_id__icontains=product_id_from_page) | Q(name__icontains=product_id_from_page))
    product_list = functions.get_product_dict_from_product(product_result)
    data = json.dumps(product_list, cls=DjangoJSONEncoder)
    return HttpResponse(data)


@csrf_exempt
def init_draft(request):
    user = request.user
    if request.method == "POST":
        post = request.POST
        product_counter = int(post["product_counter"])
        for i in range(1, product_counter + 1):
            product_id_index = "product_id_" + str(i)
            product_id = post[product_id_index]
            all_sku = ProductSku.objects.filter(product_id=product_id)
            for pro_sku in all_sku:
                sku_quantity_index = product_id + "_tb_quantity_" + str(pro_sku.id)
                sku_quantity = post[sku_quantity_index]
                mai_ru_jia_ge_index = product_id + "_tb_cost_" + str(pro_sku.id)
                mai_ru_jia_ge = post[mai_ru_jia_ge_index]
                mai_ru_jia_ge = float(mai_ru_jia_ge)
                if sku_quantity and mai_ru_jia_ge and mai_ru_jia_ge != 0 and sku_quantity != "0":
                    sku_quantity = int(sku_quantity)
                    mai_ru_jia_ge = float(mai_ru_jia_ge)
                    p1 = Product.objects.get(id=product_id)
                    draft_query = orderdraft.objects.filter(buyer_name=user, product_id=product_id,
                                                            chichu_id=pro_sku.id)
                    if draft_query.count() > 0:
                        draft_query[0].buy_quantity = draft_query[0].buy_quantity + sku_quantity
                        draft_query[0].save()
                    else:
                        current_time = datetime.datetime.now()
                        t_draft = orderdraft(buyer_name=user, product_id=product_id, outer_id=p1.outer_id,
                                             buy_quantity=sku_quantity, product_name=p1.name,
                                             buy_unitprice=mai_ru_jia_ge,
                                             chichu_id=pro_sku.id, product_chicun=pro_sku.name, created=current_time)
                        t_draft.save()
        return HttpResponseRedirect("/sale/dinghuo/dingdan/")
    else:
        return HttpResponseRedirect("/sale/dinghuo/dingdan/")


@csrf_exempt
def new_order(request):
    username = request.user
    all_drafts = orderdraft.objects.all().filter(buyer_name=username)
    if request.method == 'POST':
        post = request.POST
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
        orderlist.buyer_name = username
        orderlist.costofems = costofems * 100
        orderlist.receiver = receiver
        orderlist.express_company = express_company
        orderlist.express_no = express_no
        orderlist.supplier_name = supplierId
        orderlist.created = businessDate
        orderlist.updated = businessDate
        if len(remarks.strip()) > 0:
            orderlist.note = "-->" + request.user.username + " : " + remarks
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
            orderdetail1.created = current_time
            orderdetail1.updated = current_time
            orderdetail1.save()
        drafts.delete()
        log_action(request.user.id, orderlist, CHANGE, u'新建订货单')
        return HttpResponseRedirect("/sale/dinghuo/changedetail/" + str(orderlist.id))

    return render_to_response('dinghuo/shengchengorder.html', {"orderdraft": all_drafts},
                              context_instance=RequestContext(request))


def del_draft(request):
    username = request.user
    drafts = orderdraft.objects.filter(buyer_name=username)
    drafts.delete()
    return HttpResponse("")


def add_purchase(request):
    user = request.user
    ProductIDFrompage = "10802"
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
def plus_quantity(req):
    post = req.POST
    draft_id = post["draftid"]
    draft = orderdraft.objects.get(id=draft_id)
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
    log_action(req.user.id, orderlist, CHANGE,
               u'订货单{0}{1}{2}'.format((u'加一件'), orderdetail.product_name, orderdetail.product_chicun))
    log_action(req.user.id, orderdetail, CHANGE, u'%s' % (u'加一'))
    return HttpResponse("OK")


@csrf_exempt
def minusquantity(req):
    post = req.POST
    draft_id = post["draftid"]
    draft = orderdraft.objects.get(id=draft_id)
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
        OrderDetail.objects.filter(id=orderdetailid).update(buy_quantity=F('buy_quantity') - 1)
        OrderDetail.objects.filter(id=orderdetailid).update(total_price=F('total_price') - order_detail.buy_unitprice)
        OrderList.objects.filter(id=order_detail.orderlist_id).update(
            order_amount=F('order_amount') - order_detail.buy_unitprice)
        log_action(req.user.id, order_list, CHANGE,
                   u'订货单{0}{1}{2}'.format((u'减一件'), order_detail.product_name, orderdetail.product_chicun))
        log_action(req.user.id, order_detail, CHANGE, u'%s' % (u'减一'))
        if order_detail.buy_quantity == 1:
            order_detail.delete()
            return HttpResponse("deleted")
        return HttpResponse("OK")
    else:
        return HttpResponse("false")


@csrf_exempt
def minusarrived(req):
    post = req.POST
    orderdetailid = post["orderdetailid"]
    orderdetail = OrderDetail.objects.get(id=orderdetailid)
    orderlist = OrderList.objects.get(id=orderdetail.orderlist_id)
    OrderDetail.objects.filter(id=orderdetailid).update(arrival_quantity=F('arrival_quantity') - 1)
    OrderDetail.objects.filter(id=orderdetailid).update(
        non_arrival_quantity=F('buy_quantity') - F('arrival_quantity') - F('inferior_quantity'))
    Product.objects.filter(id=orderdetail.product_id).update(collect_num=F('collect_num') - 1)
    ProductSku.objects.filter(id=orderdetail.chichu_id).update(quantity=F('quantity') - 1)
    log_action(req.user.id, orderlist, CHANGE,
               u'订货单{0}{1}{2}'.format((u'入库减一件'), orderdetail.product_name, orderdetail.product_chicun))
    log_action(req.user.id, orderdetail, CHANGE, u'%s' % (u'入库减一'))
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
    log_action(req.user.id, orderlist, CHANGE, u'%s订货单' % (state and u'审核' or u'作废'))
    return HttpResponse("OK")


@csrf_exempt
def change_memo(req):
    post = req.POST
    sku_id = post["sku_id"]
    flag = post["flag"]
    sale_num = post.get("sale_num", 0)
    ding_huo_num = post.get("ding_huo_num", 0)
    pro_sku = ProductSku.objects.get(id=sku_id)
    memo = pro_sku.memo
    flag_of_state, sample_num = functions.get_num_by_memo(memo)
    if flag_of_state:
        if flag == '1':
            sample_num += 1
            pro_sku.memo = u"样品补全:" + str(sample_num)
            pro_sku.save()
            log_action(req.user.id, pro_sku, CHANGE, u' 增加样品一个')
            result_str, flag_of_memo, flag_of_more, flag_of_less = functions.get_ding_huo_status(int(sale_num),
                                                                                                 int(ding_huo_num),
                                                                                                 model_to_dict(pro_sku))
            # rep_json = {"flag":"2","memo":"'+pro_sku.memo+'"}
            # return HttpResponse(json.dumps(rep_json),content_type="application/json")
            return HttpResponse('{"flag":"1","memo":"' + pro_sku.memo + '","result_str":"' + result_str + '"}')
        elif flag == '0':
            sample_num -= 1
            if sample_num == 0:
                pro_sku.memo = ""
                pro_sku.save()
                log_action(req.user.id, pro_sku, CHANGE, u'删除备注')
                result_str, flag_of_memo, flag_of_more, flag_of_less = functions.get_ding_huo_status(int(sale_num),
                                                                                                     int(ding_huo_num),
                                                                                                     model_to_dict(
                                                                                                         pro_sku))
                return HttpResponse('{"flag":"1","memo":"' + pro_sku.memo + '","result_str":"' + result_str + '"}')
            pro_sku.memo = u"样品补全:" + str(sample_num)
            pro_sku.save()
            log_action(req.user.id, pro_sku, CHANGE, u' 减少样品一个')
            result_str, flag_of_memo, flag_of_more, flag_of_less = functions.get_ding_huo_status(int(sale_num),
                                                                                                 int(ding_huo_num),
                                                                                                 model_to_dict(pro_sku))
            return HttpResponse('{"flag":"1","memo":"' + pro_sku.memo + '","result_str":"' + result_str + '"}')
    else:
        if flag == '1':
            pro_sku.memo = u'样品补全:1'
            pro_sku.save()
            log_action(req.user.id, pro_sku, CHANGE, u'增加样品一个')
            result_str, flag_of_memo, flag_of_more, flag_of_less = functions.get_ding_huo_status(int(sale_num),
                                                                                                 int(ding_huo_num),
                                                                                                 model_to_dict(pro_sku))
            return HttpResponse('{"flag":"1","memo":"' + pro_sku.memo + '","result_str":"' + result_str + '"}')
        return HttpResponse('{"flag":"0","memo":"' + pro_sku.memo + '"}')


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
        note = "->" + req.user.username + ":" + note
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
    if len(buy_quantity.strip()) > 0 and len(buy_price.strip()) > 0 and len(orderlistid.strip()) > 0 and len(
            sku_id.strip()) > 0:
        buy_quantity, buy_price, orderlistid, sku_id = int(buy_quantity), float(buy_price), int(orderlistid), int(
            sku_id)
        pro_sku = ProductSku.objects.get(id=sku_id)
        product_id = pro_sku.product_id
        outer_id = pro_sku.product.outer_id
        product_name = pro_sku.product.name
        orderlist = OrderList.objects.get(id=orderlistid)
        product_chicun = pro_sku.properties_alias if len(
            pro_sku.properties_alias) > 0 else pro_sku.properties_name
        order = OrderDetail.objects.filter(orderlist_id=orderlistid, chichu_id=sku_id, buy_unitprice=buy_price)
        if order.count() > 0:
            ordertemp = order[0]
            ordertemp.buy_quantity = ordertemp.buy_quantity + buy_quantity
            ordertemp.total_price = ordertemp.total_price + buy_quantity * buy_price
            ordertemp.save()
            log_action(req.user.id, orderlist, CHANGE, u'订货单{0}{1}'.format((u'加一件'), ordertemp.product_name))
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
            log_action(req.user.id, orderlist, CHANGE, u'订货单{0}{1}'.format((u'加一件'), order_new.product_name))
        return HttpResponse("OK")
    return HttpResponse("False")


@csrf_exempt
def changearrivalquantity(request):
    post = request.POST
    order_detail_id = post.get("orderdetailid", "").strip()
    arrived_num = post.get("arrived_num", "0").strip()
    result = "{flag:false,num:0}"
    if len(arrived_num) > 0 and len(order_detail_id) > 0:
        arrived_num = int(arrived_num)
        order_detail_id = int(order_detail_id)
        order = OrderDetail.objects.get(id=order_detail_id)
        orderlist = OrderList.objects.get(id=order.orderlist_id)
        order.arrival_quantity = order.arrival_quantity + arrived_num
        order.non_arrival_quantity = order.buy_quantity - order.arrival_quantity - order.inferior_quantity
        Product.objects.filter(id=order.product_id).update(collect_num=F('collect_num') + arrived_num)
        ProductSku.objects.filter(id=order.chichu_id).update(quantity=F('quantity') + arrived_num)
        order.save()
        result = "{flag:true,num:" + str(order.arrival_quantity) + "}"
        log_action(request.user.id, orderlist, CHANGE,
                   u'订货单{0}{1}入库{2}件'.format(order.product_name, order.product_chicun, arrived_num))
        return HttpResponse(result)

    return HttpResponse(result)


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
            if orderlist.status == u"草稿":
                orderlist_dict['statusflag'] = True
            else:
                orderlist_dict['statusflag'] = False
            orderlists_list.append(orderlist_dict)
        return render_to_response("dinghuo/dailystats.html",
                                  {"orderlists_lists": orderlists_list, "prev_day": prev_day,
                                   "target_date": target_date, "next_day": next_day},
                                  context_instance=RequestContext(request))


class StatsByProductIdView(View):
    def getUserName(self, uid):
        try:
            return User.objects.get(pk=uid).username
        except:
            return 'none'

    def get(self, request, product_id):
        orderdetails = OrderDetail.objects.exclude(orderlist__status=u'作废').filter(product_id=product_id)
        return render_to_response("dinghuo/productstats.html",
                                  {"orderdetails": orderdetails},
                                  context_instance=RequestContext(request))


from flashsale.dinghuo.models_user import MyUser, MyGroup


class DailyWorkView(View):
    def parseEndDt(self, end_dt):
        if not end_dt:
            dt = datetime.datetime.now()
            return datetime.datetime(dt.year, dt.month, dt.day, 23, 59, 59)
        if len(end_dt) > 10:
            return functions.parse_datetime(end_dt)
        return functions.parse_date(end_dt)


    def getSourceDinghuo(self, start_dt=None, end_dt=None):
        dinghuo_qs = OrderDetail.objects.exclude(orderlist__status=u'作废').filter(created__gte=start_dt,
                                                                                 created__lte=end_dt)
        return dinghuo_qs

    def getDinghuoQuantityByPidAndSku(self, outer_id, sku_id, dinghuo_qs):
        ding_huo_qs = dinghuo_qs.filter(product_id=outer_id, chichu_id=sku_id)
        buy_quantity, effect_quantity = 0, 0
        for ding_huo in ding_huo_qs:
            buy_quantity += ding_huo.buy_quantity
            effect_quantity += ding_huo.buy_quantity - ding_huo.inferior_quantity - ding_huo.non_arrival_quantity
        return buy_quantity, effect_quantity

    def get(self, request):
        content = request.REQUEST
        today = datetime.date.today()
        shelve_fromstr = content.get("df", None)
        shelve_to_str = content.get("dt", None)
        query_time_str = content.get("showt", None)
        groupname = content.get("groupname", 0)
        dhstatus = content.get("dhstatus", '1')
        groupname = int(groupname)
        group_tuple = ('0', '采购A', '采购B', '采购C')
        target_date = today
        if shelve_fromstr:
            year, month, day = shelve_fromstr.split('-')
            target_date = datetime.date(int(year), int(month), int(day))
            if target_date > today:
                target_date = today

        shelve_from = datetime.datetime(target_date.year, target_date.month, target_date.day)
        time_to = self.parseEndDt(shelve_to_str)
        if time_to - shelve_from > datetime.timedelta(3):
            time_to = shelve_from + datetime.timedelta(3)
        query_time = self.parseEndDt(query_time_str)

        product_dicts = functions.get_product_by_date(target_date, group_tuple[groupname])
        orderqs = functions.get_source_orders(shelve_from, time_to)
        order_dict = functions.get_product_from_order(orderqs)
        ding_huo_qs = self.getSourceDinghuo(shelve_from, query_time)

        trade_list = []
        all_pro_sale = {}
        for product_dict in product_dicts:
            product_dict['prod_skus'] = []
            all_sku = ProductSku.objects.values('id', 'outer_id', 'properties_name', 'properties_alias', 'memo').filter(
                product_id=product_dict['id'])
            temp_total_sale_num = 0
            for sku_dict in all_sku:
                sale_num = functions.get_sale_num_by_sku(product_dict['outer_id'], sku_dict['outer_id'], order_dict)
                temp_total_sale_num = temp_total_sale_num + sale_num
                ding_huo_num, effect_quantity = self.getDinghuoQuantityByPidAndSku(product_dict['id'], sku_dict['id'],
                                                                                   ding_huo_qs)
                dinghuostatusstr, flag_of_memo, flag_of_more, flag_of_less = functions.get_ding_huo_status(
                    sale_num, ding_huo_num, sku_dict)
                if dhstatus == u'0' or ((flag_of_more or flag_of_less) and dhstatus == u'1') or (
                            flag_of_less and dhstatus == u'2') or (flag_of_more and dhstatus == u'3'):
                    sku_dict['sale_num'] = sale_num
                    sku_dict['dinghuo_num'] = ding_huo_num
                    sku_dict['effect_quantity'] = effect_quantity
                    sku_dict['sku_name'] = sku_dict['properties_alias'] if len(
                        sku_dict['properties_alias']) > 0 else sku_dict['properties_name']
                    sku_dict['dinghuo_status'] = dinghuostatusstr
                    sku_dict['flag_of_memo'] = flag_of_memo
                    sku_dict['flag_of_more'] = flag_of_more
                    sku_dict['flag_of_less'] = flag_of_less
                    product_dict['prod_skus'].append(sku_dict)

            product_dict['total_sale_num'] = temp_total_sale_num
            key_of_pro = product_dict['outer_id'][0:len(product_dict['outer_id']) - 1]
            if key_of_pro in all_pro_sale:
                all_pro_sale[key_of_pro]['total_sale_num'] += temp_total_sale_num
            else:
                all_pro_sale[key_of_pro] = {"total_sale_num": product_dict['total_sale_num'],
                                            "pic_path": product_dict['pic_path']}
                all_pro_sale[key_of_pro]['name'] = product_dict['name'].split("-")[0]
            trade_list.append(product_dict)
        all_pro_sale_items = sorted(all_pro_sale.items(), key=lambda d: d[1]['total_sale_num'], reverse=True)
        the_best_sale_pro = []
        if all_pro_sale_items:
            the_best_sale_pro = all_pro_sale_items[0]
        return render_to_response("dinghuo/dailywork.html",
                                  {"targetproduct": trade_list, "shelve_from": target_date, "time_to": time_to,
                                   "searchDinghuo": query_time, 'groupname': groupname, "dhstatus": dhstatus,
                                   "all_pro_sale": the_best_sale_pro},
                                  context_instance=RequestContext(request))

