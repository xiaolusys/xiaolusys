# coding=utf-8
"""
按月统计订单中的  小鹿代理  内部推广 以及非专属链接的订单 数量 分布情况

# 非专属链接 订单数量
select count(*) from flashsale_tongji_shopping where linkid=0 and shoptime between '2015-03-01' and '2015-04-01' ;
# 内部推广订单数量
select count(*) from flashsale_tongji_shopping where linkid<=134 and linkid>0 and shoptime between '2015-03-01' and '2015-04-01' ;
# 小鹿代理订单数量
select count(*) from flashsale_tongji_shopping where linkid>134 and shoptime between '2015-03-01' and '2015-04-01' ;

"""
from django.db import connection
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
import datetime


@csrf_exempt
def by_Linkid_Analysis(request):
    content = request.POST
    time_from = content.get("time_from", None)
    time_to = content.get("time_to", None)

    # 外部非专属
    sql1 = "select count(*) from flashsale_tongji_shopping where linkid=0 and shoptime " \
           "between '{0}' and '{1}' ".format(time_from, time_to)
    # 内部专属
    sql2 = "select count(*) from flashsale_tongji_shopping where linkid<=134 and linkid>0 and shoptime " \
           "between '{0}' and '{1}' ;".format(time_from, time_to)
    # 代理专属
    sql3 = "select count(*) from flashsale_tongji_shopping where linkid>134 and shoptime " \
           "between '{0}' and '{1}' ;".format(time_from, time_to)

    outer_raw = order_num(sql1)
    inner_raw = order_num(sql2)
    mm_raw = order_num(sql3)
    result_list = raw_handler(outer_raw=outer_raw, mm_raw=mm_raw, inner_raw=inner_raw)
    print time_from, time_to, '时间区间', result_list
    return HttpResponse(json.dumps(result_list, cls=DjangoJSONEncoder), mimetype="application/json")


def show_Orderlink_Page(request):
    date_today = datetime.datetime.today()
    today = date_today.strftime("%Y-%m-%d")
    return render_to_response("order_linkid_analysis/order_linkid_analysis.html", {"today": today},
                              context_instance=RequestContext(request))


def order_num(sql=None):
    """
    查询出  sql对应的 raw
    """
    if sql:
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        cursor.close()
        return raw
    else:
        return


def raw_handler(outer_raw=None, mm_raw=None, inner_raw=None):
    """
    处理sql的raw 两个类别的raw 结果(两列，键-值)
    返回 合并后的元组列表
    """
    outer_order_num = outer_raw[0][0]
    mm_order_num = mm_raw[0][0]
    inner_order_num = inner_raw[0][0]

    sum_order = outer_order_num + mm_order_num + inner_order_num
    percent_func = lambda num, sum_order: 0 if sum_order == 0 else round(float(num) / sum_order, 3)

    outer_per = percent_func(outer_order_num, sum_order)
    mm_per = percent_func(mm_order_num, sum_order)
    inner_per = percent_func(inner_order_num, sum_order)
    result_lit = [[u"非专属链接", outer_order_num, outer_per], [u"代理专属链接", mm_order_num, mm_per],
                  [u"内部专属链接", inner_order_num, inner_per], [u"订单总数", sum_order, 1]]
    return result_lit
