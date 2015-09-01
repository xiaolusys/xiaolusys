# -*- coding:utf8 -*-
from django.shortcuts import render_to_response, render
from django.views.decorators.csrf import csrf_exempt
from shopback.trades.models import (
    MergeTrade,
    MergeOrder,
    ReplayPostTrade,
    GIFT_TYPE,
    SYS_TRADE_STATUS,
    TAOBAO_TRADE_STATUS,
    SHIPPING_TYPE_CHOICE,
    TAOBAO_ORDER_STATUS)
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework import authentication
from rest_framework.renderers import JSONRenderer,TemplateHTMLRenderer,BrowsableAPIRenderer
from rest_framework.response import Response


def check_order(request, trade_id):
    info = MergeTrade.objects.get(id=trade_id)
    return render(request, 'trades/New_check_order.html', {'info': info})


class ChaiTradeView(APIView):
    """ docstring for class TimerOrderStatisticsView """

    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def post(self, request, *args, **kwargs):
        user = request.user
        order_list_str = request.data.get("data", None)
        if not order_list_str or len(order_list_str) == 0:
            return Response({"result": "NO ORDER"})
        result = split_merge_trade(order_list_str,user)
        return Response({"result": result})


from shopback.paramconfig import INVALID_STATUS, IN_EFFECT
from shopback.base import log_action, CHANGE, ADDITION
from django.db import transaction
from shopback.items.models import Product
from django.db.models import Q


@transaction.commit_on_success
def split_merge_trade(merger_order_id, modify_user):
    """
        批量拆单功能实现
        参数为order_id 以逗号拼接的字串
    """


    order_list = merger_order_id.split(",")
    if len(order_list) == 0:
        return "error"

    m = MergeOrder.objects.filter(Q(id=order_list[0], sys_status=IN_EFFECT))
    if m.count() == 0:
        return "error"
    parent_trade = m[0].merge_trade
    parent_trade_tid = parent_trade.tid.split("-")[0]
    first_p = Product.objects.filter(outer_id=m[0].outer_id)
    if first_p.count() == 0:
        return "error"
    payment = 0
    for order_id in order_list:
        m = MergeOrder.objects.filter(Q(id=order_id, sys_status=IN_EFFECT))
        if m.count() == 0:
            return "error"
        if parent_trade.id != m[0].merge_trade.id:
            return "error"

        p = Product.objects.filter(outer_id=m[0].outer_id)
        if p.count() == 0:
            return "error"
        if first_p[0].ware_by != p[0].ware_by:
            return "error"
        payment += m[0].payment

    count = 1
    while True:
        temp_merge = MergeTrade.objects.filter(Q(tid=parent_trade_tid + "-" + str(count)))
        if temp_merge.count() == 0:
            break
        count += 1

    parent_trade_dict = parent_trade.__dict__
    new_trade = MergeTrade(tid=parent_trade_tid + "-" + str(count), user=parent_trade.user)

    # 复制原来的订单的信息
    for k, v in parent_trade_dict.items():
        if not (k == u"tid" or k == u"id"):
            if k == u"payment":
                new_trade.payment = payment
            elif k == u"ware_by":
                new_trade.ware_by = p[0].ware_by
            else:
                hasattr(new_trade, k) and setattr(new_trade, k, v)

    new_trade.save()
    log_action(modify_user.id, new_trade, ADDITION, u'从订单{0}拆过来'.format(parent_trade.id))
    # 将新的order合入新的订单
    for order_id in order_list:
        mergeorder = MergeOrder.objects.get(id=order_id, sys_status=IN_EFFECT)
        mergeorder_dict = mergeorder.__dict__

        new_order = MergeOrder()
        for k1, v1 in mergeorder_dict.items():
            if not k1 == u"id":
                if k1 == u'merge_trade_id':
                    new_order.merge_trade_id = new_trade.id
                else:
                    hasattr(new_order, k1) and setattr(new_order, k1, v1)

        new_order.save()

        mergeorder.sys_status = INVALID_STATUS
        mergeorder.save()
        log_action(modify_user.id, mergeorder, CHANGE, u'被拆单')
    parent_trade.sys_memo += u"拆单到{0}".format(new_trade.id)
    parent_trade.save()
    log_action(modify_user.id, parent_trade, CHANGE, u'拆到订单{0}'.format(new_trade.id))
    return "OK"