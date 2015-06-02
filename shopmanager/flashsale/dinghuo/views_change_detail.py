# coding:utf-8
__author__ = 'yann'

from django.shortcuts import render_to_response
from shopback.items.models import Product
from flashsale.dinghuo.models import OrderDetail, OrderList
from django.forms.models import model_to_dict
from django.template import RequestContext
from flashsale.dinghuo import log_action, CHANGE
from django.views.generic import View
from flashsale.dinghuo.models import orderdraft
import functions
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F
from django.http import HttpResponse


class ChangeDetailView(View):
    @staticmethod
    def get(request, order_detail_id):
        order_list = OrderList.objects.get(id=order_detail_id)
        order_details = OrderDetail.objects.filter(orderlist_id=order_detail_id)
        flag_of_status = False
        flag_of_question = False
        order_list_list = []
        for order in order_details:
            order_dict = model_to_dict(order)
            order_dict['pic_path'] = Product.objects.get(id=order.product_id).pic_path
            order_list_list.append(order_dict)
        if order_list.status == "草稿":
            flag_of_status = True
        elif order_list.status == u'有问题':
            flag_of_question = True

        return render_to_response("dinghuo/changedetail.html",
                                  {"orderlist": order_list, "flagofstatus": flag_of_status,
                                   "flagofquestion": flag_of_question,
                                   "orderdetails": order_list_list},
                                  context_instance=RequestContext(request))

    @staticmethod
    def post(request, order_detail_id):
        post = request.POST
        order_list = OrderList.objects.get(id=order_detail_id)
        status = post.get("status", "").strip()
        remarks = post.get("remarks", "").strip()
        if len(status) > 0 and len(remarks) > 0:
            order_list.status = status
            order_list.note = order_list.note + "-->" + request.user.username + ":" + remarks
            order_list.save()
            log_action(request.user.id, order_list, CHANGE, u'%s 订货单' % (u'添加备注'))
        order_details = OrderDetail.objects.filter(orderlist_id=order_detail_id)
        order_list_list = []
        for order in order_details:
            order.non_arrival_quantity = order.buy_quantity - order.arrival_quantity - order.inferior_quantity
            order.save()
            order_dict = model_to_dict(order)
            order_dict['pic_path'] = Product.objects.get(id=order.product_id).pic_path
            order_list_list.append(order_dict)
        if order_list.status == "草稿":
            flag_of_status = True
        else:
            flag_of_status = False
        return render_to_response("dinghuo/changedetail.html", {"orderlist": order_list, "flagofstatus": flag_of_status,
                                                                "orderdetails": order_list_list},
                                  context_instance=RequestContext(request))


class AutoNewOrder(View):
    @staticmethod
    def get(request, order_list_id):
        user = request.user
        functions.save_draft_from_detail_id(order_list_id, user)
        all_drafts = orderdraft.objects.all().filter(buyer_name=user)
        return render_to_response("dinghuo/shengchengorder.html", {"orderdraft": all_drafts},
                                  context_instance=RequestContext(request))


@csrf_exempt
def change_inferior_num(request):
    post = request.POST
    flag = post['flag']
    order_detail_id = post["order_detail_id"].strip()
    if flag == "0":
        OrderDetail.objects.filter(id=order_detail_id).update(inferior_quantity=F('inferior_quantity') - 1)
        OrderDetail.objects.filter(id=order_detail_id).update(
            non_arrival_quantity=F('buy_quantity') - F('arrival_quantity') - F('inferior_quantity'))
        return HttpResponse("OK")
    elif flag == "1":
        OrderDetail.objects.filter(id=order_detail_id).update(inferior_quantity=F('inferior_quantity') + 1)
        OrderDetail.objects.filter(id=order_detail_id).update(
            non_arrival_quantity=F('buy_quantity') - F('arrival_quantity') - F('inferior_quantity'))
        return HttpResponse("OK")
    return HttpResponse("false")