# coding: utf-8
from .models import OrderList, PrintRecord
from django.shortcuts import render_to_response
import time
from shopmanager.shopapp.zhongtong.ztjiekou import zhongtong
from shopback.trades.models import MergeTrade

#...........======..............

#（测试）打印模版
def ztprint(request):

    orderlist(request)

    tt = {'tt':360024139575}
    return render_to_response('timi.html',{'tu':tt})

#下订单
def place_order(request,oid):

    ol = OrderList.objects.get(cus_oid=oid)

    data = "{'id': '130520142013234','tradeid': '2701843','seller': '1023123709','buyer': '6123928182','sender': {'id': '130520142010','name': '李九','company': '新南有限公司','mobile': '13912345678','phone': '021-87654321','area': '310118','city': '上海市,上海市,杨浦区','address': '华新镇华志路110号','zipcode': '610012','email': 'll@abc.com','im': '1924656234','starttime': '2013-05-20 12:00:00','endtime': '2013-05-20 15:00:00'},'receiver': {'id': '130520142097','name': '杨逸嘉','company': '逸嘉实业有限公司','mobile': '13687654321','phone': '010-22226789','area': '501022','city': '四川省,成都市,武侯区','address': '育德路497号','zipcode': '610012','email': 'yyj@abc.com','im': 'yangyijia-abc'},'items': [{'id': '1234567','name': '迷你风扇','category': '电子产品','material': '金属','size': '12,11,23','weight': '0.752','unitprice': '79','url': 'http://www.abc.com/123.html','quantity': '1','remark': '黑色大号'},{'name': 'USB3.0集线器','quantity': '1','remark': ''}],'weight': '0.753','size': '12,23,11','quantity': '2','price': '126.50','freight': '10.00','premium': '0.50','pack_charges': '1.00','other_charges': '0.00','order_sum': '0.00','collect_moneytype': 'CNY','collect_sum': '12.00','remark': '请勿摔货'}"
    zhi = zhongtong.handle_demon(data, "order.batch_submit")
    print "运单号：", zhi.keys.mailno
    ol.out_sid =zhi.keys.mailno
    ol.save()

#打印记录
def printrecord(request, m):

    pr = PrintRecord()
    if pr.record_name == u'':
        pr.record_name = request.user.username
    pr.out_sid     = m.out_sid
    pr.record_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    pr.weight      = m.weight
    pr.receiver_name  = m.receiver_name
    pr.receiver_state = m.receiver_state
    pr.receiver_city  = m.receiver_city
    pr.receiver_district = m.receiver_district
    pr.receiver_address  = m.receiver_address
    pr.receiver_zip      = m.receiver_zip
    pr.receiver_mobile   = m.receiver_mobile
    pr.receiver_phone    = m.receiver_phone
    pr.save()

#获取中通订单
def orderlist(request):

    mt = MergeTrade.objects.filter(logistics_company=500)

    for m in mt:
        ol = OrderList()
        ol.yid     = m.tid
        ol.cus_oid = m.id
        ol.out_sid = m.out_sid
        ol.type    = m.type
        ol.weight  = m.weight
        ol.created = m.created
        ol.consign_time   = m.consign_time
        ol.receiver_name  = m.receiver_name
        ol.receiver_state = m.receiver_state
        ol.receiver_city  = m.receiver_city
        ol.receiver_district= m.receiver_district
        ol.receiver_address = m.receiver_address
        ol.receiver_zip   = m.receiver_zip
        ol.receiver_mobile  = m.receiver_mobile
        ol.receiver_phone = m.receiver_phone
        ol.order_status   = m.status
        ol.save()
