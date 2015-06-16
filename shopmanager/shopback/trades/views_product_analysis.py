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
from django.db.models import Q


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


def get_source_orders(start_dt=None, end_dt=None):
    """获取某个时间段里面的原始订单的信息"""
    order_qs = MergeOrder.objects.filter(sys_status=pcfg.IN_EFFECT) \
        .exclude(merge_trade__type=pcfg.REISSUE_TYPE) \
        .exclude(merge_trade__type=pcfg.EXCHANGE_TYPE) \
        .exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE)
    order_qs = order_qs.filter(pay_time__gte=start_dt, pay_time__lte=end_dt)
    order_qs = order_qs.filter(merge_trade__status__in=pcfg.ORDER_SUCCESS_STATUS) \
        .exclude(merge_trade__sys_status__in=(pcfg.INVALID_STATUS, pcfg.ON_THE_FLY_STATUS)) \
        .exclude(merge_trade__sys_status=pcfg.FINISHED_STATUS, merge_trade__is_express_print=False)

    order_qs = order_qs.values("outer_id", "num", "outer_sku_id", "pay_time").extra(where=["CHAR_LENGTH(outer_id)>=9"]) \
        .filter(Q(outer_id__startswith="9") | Q(outer_id__startswith="1") | Q(outer_id__startswith="8"))
    return order_qs




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

    # 统计每月销售top50 及供应商
    sql = "SELECT " \
                "merge_detail.outer_id, " \
                "merge_detail.title, " \
                "merge_detail.sum_num, " \
                "dinghuo_list.supplier_name " \
            "FROM " \
                "(SELECT " \
                    "merge_order.outer_id, " \
                        "merge_order.title, " \
                        "merge_order.sum_num, " \
                        "dinghuo_detail.orderlist_id " \
                "FROM " \
                    "(SELECT " \
                    "outer_id, title, SUM(num) AS sum_num " \
                "FROM " \
                    "shop_trades_mergeorder " \
                "WHERE " \
                    "refund_status = 'NO_REFUND' " \
                        "AND status = 'TRADE_FINISHED' " \
                        "AND sys_status = 'IN_EFFECT' " \
                        "AND pay_time BETWEEN '{0}' AND '{1}' " \
                "GROUP BY outer_id " \
                "ORDER BY sum_num DESC " \
                "LIMIT 50) AS merge_order " \
                "LEFT JOIN (SELECT " \
                    "orderlist_id, outer_id " \
                "FROM " \
                    "suplychain_flashsale_orderdetail) AS dinghuo_detail ON dinghuo_detail.outer_id = merge_order.outer_id) AS merge_detail " \
                    "LEFT JOIN  " \
                "suplychain_flashsale_orderlist AS dinghuo_list ON merge_detail.orderlist_id = dinghuo_list.id".format(date_from, date_to)

    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()
    return render_to_response('product_analysis/product_analysis.html', {'data': raw, 'date_dic': date_dic},
                              context_instance=RequestContext(request))
