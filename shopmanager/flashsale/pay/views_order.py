# -*- encoding:utf8 -*-
import json
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, render
from django.template import RequestContext

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth import authenticate, login as auth_login, SESSION_KEY
from shopback.items.models import Product, ProductSku, ProductCategory
from .models import SaleTrade, SaleOrder, genUUID, Customer
from .models_refund import SaleRefund
from .tasks import confirmTradeChargeTask
from flashsale.xiaolumm.models import CarryLog, XiaoluMama
import time
import datetime
from  django.db.models import Q
from shopback.logistics import getLogisticTrace

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import logging
from core.options import log_action, ADDITION, CHANGE

logger = logging.getLogger(__name__)

ISOTIMEFORMAT = '%Y-%m-%d '
today = datetime.date.today()
real_today = datetime.date.today().strftime("%Y-%m-%d ")

start = 0
end = 100


# 查询功能
def search_flashsale(request):
    print '数字是', 4444
    if request.method == "POST":
        rec1 = []
        number1 = request.POST.get('condition')
        number = number1.strip()
        # print '数字是',number
        if number == "":
            rec1 = []
        else:
            trade_info = SaleTrade.objects.filter(
                Q(receiver_mobile=number) | Q(tid=number) | Q(buyer_nick=number) | Q(receiver_phone=number) | Q(
                    out_sid=number))
            for item in trade_info:
                info = {}
                try:
                    a = getLogisticTrace(item.out_sid, item.logistics_company.code)
                except:
                    a = []
                # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
                print '全部信息是', a
                info['trans'] = a
                info['trade'] = item
                info['detail'] = []
                for order_info in item.sale_orders.all():
                    sum = {}
                    sum['order'] = order_info
                    try:
                        product_info = Product.objects.get(outer_id=order_info.outer_id)
                    except:
                        product_info = []
                    # product_info=Product.objects.get(outer_id=order_info.outer_id)
                    sum['product'] = product_info
                    info['detail'].append(sum)
                rec1.append(info)
                print rec1
        return render(request, 'pay/order_flash.html',
                      {'info': rec1, 'time': real_today, 'yesterday': today, 'start': start})
    else:
        rec1 = []

        return render(request, 'pay/order_flash.html',
                      {'info': rec1, 'time': real_today, 'yesterday': today, 'start': start})


def order_flashsale(request):
    global today
    global start
    global end
    start = 0
    end = 100
    today = datetime.date.today()  ##14：24  改正now 改为now2
    now2 = today.strftime("%Y-%m-%d ")
    now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
    # print '现在',now4
    # print '现在',now5
    rec2 = []
    # a=  getLogisticTrace('718844325420','中通')
    # print '物流信息',a[0][0]
    trade_info = SaleTrade.objects.all().order_by('-created')[start:end]
    # print type(a)
    for item in trade_info:
        print '邮编是', item.out_sid
        info = {}
        try:
            a = getLogisticTrace(item.out_sid, item.logistics_company.code)
        except:
            a = []
        print '全部信息是', a
        info['trans'] = a
        info['trade'] = item
        info['detail'] = []
        for order_info in item.sale_orders.all():
            sum = {}
            sum['order'] = order_info
            try:
                product_info = Product.objects.get(outer_id=order_info.outer_id)
            except:
                product_info = []
            sum['product'] = product_info
            info['detail'].append(sum)
        rec2.append(info)
    return render(request, 'pay/order_flash.html',
                  {'info': rec2, 'time': real_today, 'yesterday': today, 'start': start})


def preorder_flashsale(request):
    global today
    global start
    global end
    today = datetime.date.today()  ##14：24  改正now 改为now2
    now2 = today.strftime("%Y-%m-%d ")
    now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
    # print '现在',now4
    # print '现在',now5
    rec = []
    # print '现在',start
    # print '现在',end
    if start == 0:
        start = 0
        end = 100
    else:
        start = start - 100
        end = end - 100
    # print '现在',start
    # print '现在',end
    # trade_info=SaleTrade.objects.all()[start:end]
    trade_info = SaleTrade.objects.all().order_by('-created')[start:end]
    for item in trade_info:
        info = {}
        try:
            a = getLogisticTrace(item.out_sid, item.logistics_company.code)
        except:
            a = []
        # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
        # print '全部信息是',a
        info['trans'] = a
        info['trade'] = item
        info['detail'] = []
        for order_info in item.sale_orders.all():
            sum = {}
            sum['order'] = order_info
            # product_info=Product.objects.get(outer_id=order_info.outer_id)
            try:
                product_info = Product.objects.get(outer_id=order_info.outer_id)
            except:
                product_info = []
            sum['product'] = product_info
            info['detail'].append(sum)
        rec.append(info)
    return render(request, 'pay/order_flash.html',
                  {'info': rec, 'time': real_today, 'yesterday': today, 'start': start})


def nextorder_flashsale(request):
    global today
    global start
    global end
    today = datetime.date.today()  ##14：24  改正now 改为now2
    now2 = today.strftime("%Y-%m-%d ")
    now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
    # print '现在',now4
    # print '现在',now5
    rec = []
    start = start + 100
    end = end + 100
    # print '现在',start
    # print '现在',end
    # trade_info=SaleTrade.objects.all()[start:end]
    trade_info = SaleTrade.objects.all().order_by('-created')[start:end]
    for item in trade_info:
        info = {}
        # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
        try:
            a = getLogisticTrace(item.out_sid, item.logistics_company.code)
        except:
            a = []
            # print '全部信息是',a
        info['trans'] = a
        info['trade'] = item
        info['detail'] = []
        for order_info in item.sale_orders.all():
            sum = {}
            sum['order'] = order_info
            # product_info=Product.objects.get(outer_id=order_info.outer_id)
            try:
                product_info = Product.objects.get(outer_id=order_info.outer_id)
            except:
                product_info = []
            sum['product'] = product_info
            info['detail'].append(sum)
        rec.append(info)
    return render(request, 'pay/order_flash.html',
                  {'info': rec, 'time': real_today, 'yesterday': today, 'start': start})


def order_flashsale22(request):
    global today
    today = datetime.date.today()  # 14：24  改正now 改为now2
    now2 = today.strftime("%Y-%m-%d ")
    now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
    # print '现在',now4
    # print '现在',now5
    rec = []
    trade_info = SaleTrade.objects.filter(created__range=(now4, now5))
    for item in trade_info:
        info = {}
        info['trade'] = item
        info['detail'] = []
        for order_info in item.sale_orders.all():
            sum = {}
            sum['order'] = order_info
            product_info = Product.objects.get(outer_id=order_info.outer_id)
            sum['product'] = product_info
            info['detail'].append(sum)
        rec.append(info)
    return render(request, 'pay/order_flash.html', {'info': rec, 'time': real_today, 'yesterday': today})


def time_rank(request, time_id):
    global today
    realtoday = datetime.date.today().strftime("%Y-%m-%d ")  # 真正的今天的时间
    day = time_id
    print int(day), type(day)
    if int(day) == 1:
        today = today - datetime.timedelta(days=1)
        now2 = today.strftime("%Y-%m-%d ")
        now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
        now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
        # print '现在',now4
        # print '现在',now5
        rec = []
        trade_info = SaleTrade.objects.filter(created__range=(now4, now5))
        for item in trade_info:
            info = {}
            info['trade'] = item
            info['detail'] = []
            try:
                a = getLogisticTrace(item.out_sid, item.logistics_company.code)
            except:
                a = []
            # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
            print '全部信息是', a
            info['trans'] = a
            for order_info in item.sale_orders.all():
                sum = {}
                print 'orderinfo', order_info
                print 'order2', order_info.outer_id
                sum['order'] = order_info
                try:
                    product_info = Product.objects.get(outer_id=order_info.outer_id)
                except:
                    product_info = []
                # product_info=Product.objects.get(outer_id=order_info.outer_id)
                sum['product'] = product_info
                info['detail'].append(sum)
            rec.append(info)
            # print '本次结束',   rec
            # print rec
        return render(request, 'pay/order_flash.html', {'info': rec, 'time': real_today, 'yesterday': today})


    elif int(day) == 0:
        today = datetime.date.today()
        now2 = today.strftime("%Y-%m-%d ")  # 14：24  改正now 改为now2
        print '今天是', type(now2)
        rec = []
        today = datetime.date.today()
        now2 = today.strftime("%Y-%m-%d ")
        now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
        now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
        trade_info = SaleTrade.objects.filter(created__range=(now4, now5))
        print '现在', now4
        print '现在', now5
        for item in trade_info:
            info = {}
            try:
                a = getLogisticTrace(item.out_sid, item.logistics_company.code)
            except:
                a = []
            # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
            # print '全部信息是',a
            info['trans'] = a
            info['trade'] = item
            info['detail'] = []
            for order_info in item.sale_orders.all():
                sum = {}
                # print 'orderinfo' ,  order_info
                # print 'order2' ,  order_info.outer_id
                sum['order'] = order_info
                try:
                    product_info = Product.objects.get(outer_id=order_info.outer_id)
                except:
                    product_info = []
                # product_info=Product.objects.get(outer_id=order_info.outer_id)
                # print product_info,'tttttt'
                sum['product'] = product_info
                info['detail'].append(sum)
            rec.append(info)
            # print '本次结束',   rec
            # print rec
        return render(request, 'pay/order_flash.html', {'info': rec, 'time': real_today, 'yesterday': today})

    elif int(day) == 2:
        if today.strftime("%Y-%m-%d ") == realtoday:
            today = datetime.date.today()
        else:
            today = today + datetime.timedelta(days=1)
        now2 = today.strftime("%Y-%m-%d ")
        now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
        now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
        trade_info = SaleTrade.objects.filter(created__range=(now4, now5))
        rec = []
        for item in trade_info:
            info = {}
            try:
                a = getLogisticTrace(item.out_sid, item.logistics_company.code)
            except:
                a = []
            # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
            # print '全部信息是',a
            info['trans'] = a
            info['trade'] = item
            info['detail'] = []
            for order_info in item.sale_orders.all():
                sum = {}
                # print 'orderinfo' ,  order_info
                # print 'order2' ,  order_info.outer_id
                sum['order'] = order_info
                # product_info=Product.objects.get(outer_id=order_info.outer_id)
                try:
                    product_info = Product.objects.get(outer_id=order_info.outer_id)
                except:
                    product_info = []
                    # print product_info,'tttttt'
                sum['product'] = product_info
                info['detail'].append(sum)
            rec.append(info)
        return render(request, 'pay/order_flash.html', {'info': rec, 'time': real_today, 'yesterday': today})

        # 增加交易状态的处理


def sale_state(request, state_id):
    print '编号', type(state_id)
    print '状态是', state_id
    global today
    print today
    now2 = today.strftime("%Y-%m-%d ")
    now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
    rec = []
    trade_info = SaleTrade.objects.filter(created__range=(now4, now5))
    for item in trade_info:
        info = {}
        try:
            a = getLogisticTrace(item.out_sid, item.logistics_company.code)
        except:
            a = []
        # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
        # print '全部信息是',a
        info['trans'] = a
        info['trade'] = item
        info['detail'] = []
        # print 'order1' ,  item.sale_orders.all()
        for order_info in item.sale_orders.all():
            sum = {}
            # print 'orderinfo' ,  order_info
            # print 'order2' ,  order_info.outer_id
            sum['order'] = order_info
            try:
                product_info = Product.objects.get(outer_id=order_info.outer_id)
            except:
                product_info = []
                # product_info=Product.objects.get(outer_id=order_info.outer_id)
                # print product_info,'tttttt'
            sum['product'] = product_info
            info['detail'].append(sum)
            # print '状态2是' ,  item.status
        if item.status == long(state_id):
            rec.append(info)
            # print '本次结束',   rec
    # print rec
    return render(request, 'pay/order_flash.html', {'info': rec, 'time': real_today, 'yesterday': today})


# 退款状态
def refund_state(request, state_id):
    # print '编号' , type( state_id)
    # print '状态是' ,  state_id
    global today
    # print today
    now2 = today.strftime("%Y-%m-%d ")
    now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
    trade_info = SaleTrade.objects.filter(created__range=(now4, now5))
    rec = []
    # print 'order0' ,  trade_info
    for item in trade_info:
        info = {}
        try:
            a = getLogisticTrace(item.out_sid, item.logistics_company.code)
        except:
            a = []
            # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
            # print '全部信息是',a
        info['trans'] = a
        info['trade'] = item
        info['detail'] = []
        for order_info in item.sale_orders.all():
            sum = {}
            # print 'orderinfo' ,  order_info
            #  print 'order2' ,  order_info.outer_id
            sum['order'] = order_info
            # product_info=Product.objects.get(outer_id=order_info.outer_id)
            try:
                product_info = Product.objects.get(outer_id=order_info.outer_id)
            except:
                product_info = []
                # print product_info,'tttttt'
            sum['product'] = product_info
            info['detail'].append(sum)
            if order_info.refund_status == long(state_id):
                rec.append(info)
                # print '本次结束',   rec
    # print rec
    return render(request, 'pay/order_flash.html', {'info': rec, 'time': real_today, 'yesterday': today})


def refunding_state(request, state_id):
    # print '编号' , type( state_id)
    # print '状态是' ,  state_id
    global today
    now2 = today.strftime("%Y-%m-%d ")
    now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
    rec = []
    trade_info = SaleTrade.objects.filter(created__range=(now4, now5))
    # print 'order0' ,  trade_info
    for item in trade_info:
        info = {}
        try:
            a = getLogisticTrace(item.out_sid, item.logistics_company.code)
        except:
            a = []
        # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
        # print '全部信息是',a
        info['trans'] = a
        info['trade'] = item
        info['detail'] = []
        # print 'order1' ,  item.sale_orders.all()
        for order_info in item.sale_orders.all():
            sum = {}
            # print 'orderinfo' ,  order_info
            # print 'order2' ,  order_info.outer_id
            sum['order'] = order_info
            # product_info=Product.objects.get(outer_id=order_info.outer_id)
            try:
                product_info = Product.objects.get(outer_id=order_info.outer_id)
            except:
                product_info = []
            # print product_info,'tttttt'
            sum['product'] = product_info
            info['detail'].append(sum)
            if order_info.refund_status != long(0) and order_info.refund_status != long(7):
                rec.append(info)
                # print '本次结束',   rec
                # print rec

    return render(request, 'pay/order_flash.html', {'info': rec, 'time': real_today, 'yesterday': today})


def change_sku_item(request):
    content = request.REQUEST
    sale_order_id = int(content.get("sale_order_id", None))
    sku = content.get("SKU")
    if not sku:
        return HttpResponse({False})
    if not ProductSku.objects.filter(id=sku).exists():
        return HttpResponse({False})
    num = content.get("num", None)
    try:
        num = int(num)
    except:
        return HttpResponse({False})
    sale_order = get_object_or_404(SaleOrder, id=sale_order_id)
    sale_trade = sale_order.sale_trade
    try:
        sale_trade.change_sku_item(sale_order, sku, num)
    except Exception, e0:
        return HttpResponse(json.dumps({'status': 1, "desc": str(e0)}))
    return HttpResponse(True)


def refund_fee(request):
    content = request.REQUEST
    sale_order = int(content.get("sale_order_id", None))
    refund_fee = float(content.get("refund_fee", None))
    return_goods_info = {}
    sale_order = get_object_or_404(SaleOrder, id=sale_order)  # 退款sale_order对象
    refund_info = {"return_good": False, "refund_fee": refund_fee, "reason": "", "desc": ""}

    if sale_order.status != sale_order.__class__.WAIT_SELLER_SEND_GOODS:  # 状态为已付款
        logger.error("交易状态不是已付款状态")
        return HttpResponse("交易状态不是已付款状态")

    sale_trader = sale_order.sale_trade  # 退款sale_trade对象
    reason = ' '  # 退款理由
    refund_num = None  # 退款件数
    # 在saleorder订单状态为已经付款情况下，生成退款单salerefund，把退款单id 退款和退款状态赋值给sale_order中的三个字段
    try:
        s = SaleRefund(
            trade_id=sale_order.sale_trade.id,
            order_id=sale_order.id,
            buyer_id=sale_order.buyer_id,
            item_id=sale_order.item_id,
            charge=sale_trader.charge,
            channel=sale_trader.channel,
            sku_id=sale_order.sku_id,
            sku_name=sale_order.sku_name,
            refund_num=sale_order.num,
            buyer_nick=sale_trader.buyer_nick,
            mobile=sale_trader.receiver_mobile,
            phone=sale_trader.receiver_mobile,
            total_fee=sale_order.total_fee,
            payment=sale_order.payment,
            refund_fee=sale_order.payment,
            title=sale_order.title,
            reason=reason,
            good_status=SaleRefund.SELLER_OUT_STOCK,
            status=SaleRefund.REFUND_WAIT_SELLER_AGREE,
        )
        s.save()
        sale_order.refund_id = s.id
        sale_order.refund_fee = s.refund_fee
        sale_order.refund_status = s.status
        sale_order.save()
        log_action(request.user, sale_order, CHANGE, 'SaleOrder订单退款')
        log_action(request.user, s, CHANGE, 'SaleRefund退款单创建')
        return HttpResponse("退款申请成功!")
    except Exception, exc:
        logger.error('gen_out_stock_refund: %s.' % exc.message)
        return HttpResponse("生成退款单出错！")

    #s = SaleRefund.gen_out_stock_refund(sale_order_id)

    # if s == True:
    #     return  HttpResponse(True)
    # else:
    #     return HttpResponse(s)
