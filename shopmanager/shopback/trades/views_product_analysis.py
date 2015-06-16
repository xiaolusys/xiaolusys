# coding=utf-8
__author__ = 'linjie'
from django.shortcuts import render_to_response
from django.template import RequestContext
from models import MergeTrade, MergeOrder
import datetime
from django.db.models import Sum
from shopback import paramconfig as pcfg
from flashsale.dinghuo.models import OrderDetail
from flashsale.clickrebeta.models import StatisticsShopping
from django.db.models import connection
from flashsale.xiaolumm.models import XiaoluMama
from django.views.decorators.csrf import csrf_exempt


def get_Month_By_Date(date_time):
    day_from = datetime.date(date_time.year, date_time.month, 1)  # 这个月的开始时间
    if date_time.month == 12:
        day_to = datetime.date(date_time.year, date_time.month, 31)
    else:
        day_to = datetime.date(date_time.year, date_time.month + 1, 1) - datetime.timedelta(1)  # 下个月的第一天减去1天
    date_from = datetime.datetime(day_from.year, day_from.month, day_from.day, 0, 0, 0)
    date_to = datetime.datetime(day_to.year, day_to.month, day_to.day, 23, 59, 59)
    return date_from, date_to



@csrf_exempt
def xlmm_Product_Analysis(request):
    content = request.REQUEST
    daystr = content.get("month", None)
    if daystr:
        year, month, day = daystr.split('-')
        target_date = datetime.datetime(int(year), int(month), int(day))
        date_from, date_to = get_Month_By_Date(target_date)
    else:
        target_date = datetime.datetime.now()
        date_from, date_to = get_Month_By_Date(target_date)
    prev_month = datetime.date(date_from.year, date_from.month, date_from.day) - datetime.timedelta(days=1)
    next_month = datetime.date(date_to.year, date_to.month, date_to.day) + datetime.timedelta(days=1)

    date_from = datetime.date(date_from.year, date_from.month, date_from.day)
    date_to = datetime.date(date_to.year, date_to.month, date_to.day)
    date_dic = {"prev_month": prev_month, "next_month": next_month}

    sql = "select success_order.linkid, success_order.linkname,success_order.mm_sum_payment ,success_order.mm_sum_num, " \
          "refund.mm_sum_payment, refund.mm_sum_num ,success_order.username, " \
          "ROUND( (IF(success_order.mm_sum_payment=0,0,100*(refund.mm_sum_payment/success_order.mm_sum_payment))) ,2)AS refun_pay_rate," \
          "ROUND( (IF(success_order.mm_sum_num=0,0,100*(refund.mm_sum_num /success_order.mm_sum_num))) ,2) AS refun_rate  from " \
          "(select wx_xx_mo.linkid, wx_xx_mo.linkname,wx_xx_mo.mm_sum_payment, wx_xx_mo.mm_sum_num,auth_user.username from " \
          "(select wx_mo.linkname  , wx_mo.linkid,  sum(wx_mo.sum_payment) as mm_sum_payment,  sum(wx_mo.sum_num) as mm_sum_num ,xx.manager from " \
          "(select mo.sum_payment, mo.sum_num, mo.oid,wx.wxorderid,wx.linkname,wx.linkid from " \
          "(SELECT sum(payment) as sum_payment,sum(num) as sum_num,oid FROM " \
          "shop_trades_mergeorder  WHERE  status='TRADE_FINISHED' and pay_time BETWEEN '{0}' AND '{1}' group by oid ) AS mo " \
          "LEFT JOIN (SELECT wxorderid,linkname,linkid FROM flashsale_tongji_shopping WHERE shoptime BETWEEN '{0}' AND '{1}' ) " \
          "AS wx ON mo.oid=wx.wxorderid) as wx_mo left join " \
          "(select id ,manager from xiaolumm_xiaolumama) as xx on wx_mo.linkid=xx.id group by wx_mo.linkid) as wx_xx_mo " \
          "left join (select id,username from auth_user) as auth_user on wx_xx_mo.manager=auth_user.id ) as success_order " \
          "left join " \
          "(  select wx_xx_mo.linkid,wx_xx_mo.mm_sum_payment, wx_xx_mo.mm_sum_num  from " \
          "(select wx_mo.linkname  , wx_mo.linkid,  sum(wx_mo.sum_payment) as mm_sum_payment,  sum(wx_mo.sum_num) as mm_sum_num ,xx.manager from " \
          "(select mo.sum_payment, mo.sum_num, mo.oid,wx.wxorderid,wx.linkname,wx.linkid from " \
          "(SELECT sum(payment) as sum_payment,sum(num) as sum_num,oid FROM " \
          "shop_trades_mergeorder  WHERE refund_status='SUCCESS' and pay_time BETWEEN '{0}' AND '{1}' group by oid ) AS mo " \
          "LEFT JOIN (SELECT wxorderid,linkname,linkid FROM flashsale_tongji_shopping WHERE shoptime BETWEEN '{0}' AND '{1}' ) " \
          "AS wx ON mo.oid=wx.wxorderid) as wx_mo left join " \
          "(select id ,manager from xiaolumm_xiaolumama) as xx on wx_mo.linkid=xx.id group by wx_mo.linkid) as wx_xx_mo " \
          "left join (select id,username from auth_user) as auth_user on wx_xx_mo.manager=auth_user.id) as refund on success_order.linkid=refund.linkid".format(
        date_from, date_to)

    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()
    return render_to_response('product_analysis/xlmm_pro_analysis.html', {'raw': raw, 'date_dic': date_dic},
                              context_instance=RequestContext(request))


@csrf_exempt
def product_Analysis(request):
    content = request.REQUEST
    daystr = content.get("month", None)
    if daystr:
        year, month, day = daystr.split('-')
        target_date = datetime.datetime(int(year), int(month), int(day))
        date_from, date_to = get_Month_By_Date(target_date)
    else:
        target_date = datetime.datetime.now()
        date_from, date_to = get_Month_By_Date(target_date)
    prev_month = datetime.date(date_from.year, date_from.month, date_from.day) - datetime.timedelta(days=1)
    next_month = datetime.date(date_to.year, date_to.month, date_to.day) + datetime.timedelta(days=1)

    date_from = datetime.date(date_from.year, date_from.month, date_from.day)
    date_to = datetime.date(date_to.year, date_to.month, date_to.day)
    date_dic = {"prev_month": prev_month, "next_month": next_month}

    data = []
    zone_orders = MergeOrder.objects.filter(created__gt=date_from, created__lt=date_to)  # 总订单

    outer_id_values = zone_orders.values('outer_id').distinct()
    for i in outer_id_values:
        dinghuo_order_details = OrderDetail.objects.filter(outer_id=i['outer_id'], created__gt=date_from,
                                                           created__lt=date_to)
        inferior_quantity = dinghuo_order_details.aggregate(inferior_quantity=Sum('inferior_quantity')).get(
            'inferior_quantity') or 0  # 次品数量
        buy_quantity = dinghuo_order_details.aggregate(buy_quantity=Sum('buy_quantity')).get(
            'buy_quantity') or 0  # 订货数量
        if buy_quantity is 0 or inferior_quantity is None:
            inferior_rate = 0.0
        else:
            inferior_rate = round((100 * float(inferior_quantity) / buy_quantity), 4)  # 次品百分比

        orders = zone_orders.filter(outer_id=i['outer_id'], status=pcfg.TRADE_FINISHED, sys_status=pcfg.IN_EFFECT)
        refund_orders = orders.filter(refund_status=pcfg.REFUND_SUCCESS)
        if orders.count() > 0:
            outer_id = orders[0].outer_id
            refund_orders_count = refund_orders.count()  # 退货订单
            market_count = orders.count()  # 同款商品的销售数量
            total_payment = orders.aggregate(total_payment=Sum('payment')).get('total_payment') or 0
            if (market_count + refund_orders_count) is 0 or None:
                refund_rate = 0.0
            else:
                refund_rate = round((100 * float(refund_orders_count) / (market_count + refund_orders_count)),
                                    4)  # 退货百分比
            data_entry = {'outer_id': outer_id, 'market_count': market_count, 'total_payment': total_payment,
                          'refund_rate': refund_rate, 'inferior_rate': inferior_rate, 'buy_quantity': buy_quantity}
            data.append(data_entry)

    return render_to_response('product_analysis/product_analysis.html', {'data': data, 'date_dic': date_dic},
                              context_instance=RequestContext(request))
