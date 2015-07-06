#-*- coding:utf8 -*-
from django.shortcuts import render_to_response,render
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
def check_order(request,trade_id):
        print "进入",trade_id
        info=MergeTrade.objects.get(id=trade_id)
        print info
        return render(request, 'trades/New_check_order.html',{'info':info})