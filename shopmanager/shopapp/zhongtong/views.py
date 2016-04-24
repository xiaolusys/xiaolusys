# coding: utf-8
import time

from django.http import HttpResponse
from django.shortcuts import render_to_response
from shopapp.zhongtong import zhongtong
from shopback.trades.models import MergeTrade
from .models import ZTOOrderList, PrintRecord


# ...........======..............

# （测试）打印模版
def ztprint(request):
    orderlist(request)

    tt = {'tt': 360024139575}
    return render_to_response('yunda_bill.html', {'tu': tt})


# 下订单
def place_order(request, oid):
    ol = ZTOOrderList.objects.get(cus_oid=oid)

    data = "{'id': '" + ol.yid + "','tradeid': '','seller': '','buyer': '','sender': {'id': '','name': '小鹿美美','company': '上海己美网络科技有限公司','mobile': '','phone': '021-87654321','area': '','city': '上海市,上海市,佘山镇','address': '吉业路245号','zipcode': '','email': '','im': '','starttime': '2013-05-20 12:00:00','endtime': '2013-05-20 15:00:00'},'receiver': {'id': '','name': '" + ol.receiver_name + "','company': '','mobile': '" + ol.receiver_mobile + "','phone': '010-22226789','area': '','city': '" + ol.receiver_state + "," + ol.receiver_city + "," + ol.receiver_district + "','address': '" + ol.receiver_address + "','zipcode': '" + ol.receiver_zip + "','email': '','im': ''},'items': [{'name': '','quantity': '','remark': ''}],'weight': '" + ol.weight + "','size': '','quantity': '2','price': '','freight': '','premium': '','pack_charges': '','other_charges': '','order_sum': '','collect_moneytype': 'CNY','collect_sum': '','remark': '" + ol.remarke + "'}"
    zhi = zhongtong.handle_demon(data, "order.submit")

    ol.consign_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    ol.out_sid = zhi['keys']['mailno']
    ol.save()


# 打印记录
def printrecord(request, m):
    pr = PrintRecord()
    if pr.record_name == u'':
        pr.record_name = request.user.username
    pr.out_sid = m.out_sid
    pr.record_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    pr.weight = m.weight
    pr.receiver_name = m.receiver_name
    pr.receiver_state = m.receiver_state
    pr.receiver_city = m.receiver_city
    pr.receiver_district = m.receiver_district
    pr.receiver_address = m.receiver_address
    pr.receiver_zip = m.receiver_zip
    pr.receiver_mobile = m.receiver_mobile
    pr.receiver_phone = m.receiver_phone
    pr.save()


# 获取中通订单
def orderlist(request):
    mt = MergeTrade.objects.filter(logistics_company=500)

    for m in mt:
        t, b = ZTOOrderList.objects.get_or_create(yid=m.tid, cus_oid=m.id, out_sid=m.out_sid, type=m.type,
                                                  weight=m.weight,
                                                  created=m.created, consign_time=m.consign_time,
                                                  receiver_name=m.receiver_name,
                                                  receiver_city=m.receiver_city, receiver_district=m.receiver_district,
                                                  receiver_address=m.receiver_address, receiver_zip=m.receiver_zip,
                                                  receiver_mobile=m.receiver_mobile, receiver_phone=m.receiver_phone)
        if b:
            t.receiver_state = m.receiver_state
            t.sys_status = m.sys_status
            t.order_status = m.status
            t.save()

    return HttpResponse("OK")
