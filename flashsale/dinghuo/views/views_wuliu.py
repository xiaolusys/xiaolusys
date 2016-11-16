# coding=utf-8
from django.shortcuts import render
from flashsale.dinghuo.models import OrderDraft, OrderDetail, OrderList
from django.views.decorators.csrf import csrf_exempt
from django.template import RequestContext
from shopback.logistics import getLogisticTrace


@csrf_exempt
def view_wuliu(req, orderdetail_id):
    orderlist = OrderList.objects.get(id=orderdetail_id)
    result = ""
    if orderlist.express_no != "" and orderlist.express_company != "":
        result = getLogisticTrace(orderlist.express_no, orderlist.express_company)
    return render(
        request,
        "dinghuo/wuliu/wuliu.html",
        {"orderlist": orderlist, 'result': result},
    )
