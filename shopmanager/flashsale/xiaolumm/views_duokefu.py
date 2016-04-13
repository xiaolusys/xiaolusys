# coding=utf-8
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render_to_response
from django.views.generic import View
from django.template import RequestContext
from shopapp.weixin.models import WeiXinUser, WXOrder
from django.views.decorators.csrf import csrf_exempt
import datetime
import json
from django.forms import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from shopback.trades.models import MergeTrade, MergeOrder
from shopback.logistics import getLogisticTrace


@csrf_exempt
def kf_Customer(request):
    # 展示用户信息
    if request.method == "POST":
        openid = request.POST.get('openid', 'oMt59uDSymShXs9JcCjLxcHdNnKA')
        weixin_user = WeiXinUser.objects.get(openid=openid)  # 没有关注的客户不会被客服
        sex = WeiXinUser.SEX_TYPE[weixin_user.sex - 1][1]  # 注意这里的Choice是从1开始的
        nickname = weixin_user.nickname
        province = weixin_user.province
        city = weixin_user.city
        address = weixin_user.address
        mobile = weixin_user.mobile
        vmobile = weixin_user.vmobile  # 待验证手机
        isvalid = weixin_user.isvalid  # 已经验证  （布尔类型）
        if isvalid is True:
            isvalid = u'已验证'
        else:
            isvalid = u'未验证'
        charge_status = weixin_user.charge_status  # 接管状态  （布尔类型）
        # 该用户推荐的数量
        referal_count = WeiXinUser.objects.filter(referal_from_openid=openid).count()

        weixin_user_data = {'openid': openid, 'province': province, 'city': city, 'address': address,
                            'sex': sex, 'nickname': nickname, 'vmobile': vmobile, 'mobile': mobile,
                            'referal_count': referal_count, 'isvalid': isvalid, 'charge_status': charge_status}
        data = []
        data.append(weixin_user_data)
        return HttpResponse(json.dumps(data), content_type='application/json')  # 返回 JSON 数据
    elif request.method == "GET":
        return render_to_response("duokefu_assist.html", {},
                                  context_instance=RequestContext(request))


@csrf_exempt
def kf_Weixin_Order(request):
    # 微信订单信息
    data = []
    if request.method == 'POST':
        openid = request.POST.get('openid', 'oMt59uDSymShXs9JcCjLxcHdNnKA')
        weixin_orders = WXOrder.objects.filter(buyer_openid=openid).order_by(
            '-order_create_time')  # 找到该用户的订单(默认显示)   注意这里可以有多个订单产生
        if weixin_orders.count() > 0:
            order_id = weixin_orders[0].order_id
            product_name = weixin_orders[0].product_name
            order_total_price = weixin_orders[0].order_total_price / 100.0
            product_price = weixin_orders[0].product_price / 100.0
            order_express_price = weixin_orders[0].order_express_price
            product_count = weixin_orders[0].product_count
            order_create_time = weixin_orders[0].order_create_time.strftime('%y/%m/%d/%H:%M')
            order_status = weixin_orders[0].get_order_status_display()
            receiver_name = weixin_orders[0].receiver_name
            mobile = weixin_orders[0].receiver_mobile
            address = weixin_orders[0].receiver_province + weixin_orders[0].receiver_city + weixin_orders[
                0].receiver_zone + weixin_orders[0].receiver_address
            delivery_id = weixin_orders[0].delivery_id
            delivery_company = weixin_orders[0].delivery_company
            product_img = weixin_orders[0].product_img

            data_entry = {
                'order_id': order_id,
                'product_name': product_name,
                'product_count': product_count,
                'order_total_price': order_total_price,
                'product_price': product_price,
                'order_express_price': order_express_price,
                'order_create_time': order_create_time,
                'order_status': order_status,
                'receiver_name': receiver_name,
                'mobile': mobile,
                'address': address,
                'delivery_id': delivery_id,
                'delivery_company': delivery_company,
                'product_img': product_img
            }
            data.append(data_entry)
        return HttpResponse(json.dumps(data), content_type='application/json')  # 返回 JSON 数据
    elif request.method == "GET":
        return render_to_response("weixin_order.html", {},
                                  context_instance=RequestContext(request))


def ke_Find_More_Weixin_Order(request):
    data = []
    openid = request.GET.get('openid')
    weixin_orders = WXOrder.objects.filter(buyer_openid=openid)
    today = datetime.datetime.today()
    time_to = today
    # 搜索一个月以内的订单
    time_from = today - datetime.timedelta(days=30)
    weixin_orders_cut = WXOrder.objects.filter(buyer_openid=openid, order_create_time__gt=time_from,
                                               order_create_time__lt=time_to).order_by('-order_create_time')[1:]

    for weixin_order in weixin_orders_cut:
        if weixin_order.order_create_time is None:
            order_create_time = ''
        else:
            order_create_time = weixin_order.order_create_time.strftime('%y/%m/%d/%H:%M')
        data_entry = {'order_id': weixin_order.order_id, 'product_img': weixin_order.product_img,
                      'order_total_price': weixin_order.order_total_price / 100.0,
                      'order_express_price': weixin_order.order_express_price / 100.0,
                      'order_create_time': order_create_time,
                      'order_status': weixin_order.get_order_status_display(),
                      'receiver_name': weixin_order.receiver_name,
                      'receiver_address': weixin_order.receiver_province + weixin_order.receiver_city + weixin_order.receiver_zone + weixin_order.receiver_address,
                      'receiver_mobile': weixin_order.receiver_mobile,
                      'product_name': weixin_order.product_name,
                      'product_price': weixin_order.product_price / 100.0,
                      'product_count': weixin_order.product_count,
                      'delivery_id': weixin_order.delivery_id,
                      'delivery_company': weixin_order.delivery_company}
        data.append(data_entry)
    return HttpResponse(json.dumps(data), content_type='application/json')  # 返回 JSON 数据


def kf_Search_Page(request):
    return render_to_response('search_order.html', {}, context_instance=RequestContext(request))


from django.db.models import Sum, Q


@csrf_exempt
def kf_Search_Order_By_Mobile(request):
    # 客服模块：按照手机号码搜索订单
    data = []
    mobile = request.GET.get('mobile')
    # 试图 查找特卖订单 Pay 中的get 到了多个订单报错  所以找到最后一个
    today = datetime.datetime.today()
    time_to = today
    # 搜索一个月以内的订单
    time_from = today - datetime.timedelta(days=30)
    merge_trades = MergeTrade.objects.filter(created__gt=time_from, created__lt=time_to).filter(
        Q(receiver_mobile=mobile) | Q(tid=mobile)).order_by('-created')
    for merge_trade in merge_trades:
        if merge_trade.consign_time is None:
            consign_time = u'未发货'
        else:
            consign_time = merge_trade.consign_time.strftime('%y/%m/%d/%H:%M')
        if merge_trade.logistics_company is None:
            logistics_company = u"未知"
        else:
            logistics_company = merge_trade.logistics_company.name  # 物流公司名称
        out_sid = merge_trade.out_sid  # 物流编号
        data_entry = {'id': merge_trade.id,
                      'tid': merge_trade.tid,
                      'status': merge_trade.get_status_display(),
                      'sys_status': merge_trade.get_sys_status_display(),
                      'receiver_name': merge_trade.receiver_name,
                      'consign_time': consign_time,
                      'address': merge_trade.receiver_state + '-' + merge_trade.receiver_city +
                                 '-' + merge_trade.receiver_district + '-' + merge_trade.receiver_address,
                      'buyer_message': merge_trade.buyer_message,
                      'seller_memo': merge_trade.seller_memo,
                      'logistics_company': logistics_company,
                      'out_sid': out_sid
                      }
        data.append(data_entry)
    return HttpResponse(json.dumps(data), content_type='application/json')  # 返回 JSON 数据


@csrf_exempt
def kf_Search_Order_Detail(request):
    merge_trade = request.GET.get('id')
    merge_orders = MergeOrder.objects.filter(merge_trade=merge_trade)
    data = []

    for merge_order in merge_orders:
        if merge_order.pay_time:
            pay_time = merge_order.pay_time.strftime('%Y-%m-%d %H:%M')
        else:
            pay_time = ''
        data_entry = {'title': merge_order.title,
                      'price': merge_order.price,
                      'sku_properties_name': merge_order.sku_properties_name,
                      'num': merge_order.num,
                      'total_fee': merge_order.total_fee,
                      'payment': merge_order.payment,
                      'pic_path': merge_order.pic_path,
                      'status': merge_order.get_status_display(),
                      'sys_status': merge_order.get_sys_status_display(),
                      'pay_time': pay_time,
                      'refund_status': merge_order.get_refund_status_display()
                      }
        data.append(data_entry)
    return HttpResponse(json.dumps(data), content_type='application/json')  # 返回 JSON 数据
