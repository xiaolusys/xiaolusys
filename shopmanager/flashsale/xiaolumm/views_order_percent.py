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
import datetime
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def by_Linkid_Analysis(request):
    content = request.POST
    time_from = content.get("time_from", None)
    time_to = content.get("time_to", None)

    # 外部非专属
    sql1 = "select count(*),sum(wxorderamount) from flashsale_tongji_shopping where linkid=0 and shoptime " \
           "between '{0}' and '{1}' and status in (0, 1);".format(time_from, time_to)
    # 内部专属
    sql2 = "select count(*),sum(wxorderamount) from flashsale_tongji_shopping where linkid<=134 and linkid>0 and shoptime " \
           "between '{0}' and '{1}' and status in (0, 1);".format(time_from, time_to)
    # 代理专属
    sql3 = "select count(*),sum(wxorderamount) from flashsale_tongji_shopping where linkid>134 and shoptime " \
           "between '{0}' and '{1}' and status in (0, 1);".format(time_from, time_to)

    outer_raw = order_num(sql1)
    inner_raw = order_num(sql2)
    mm_raw = order_num(sql3)
    result_list = raw_handler(outer_raw=outer_raw, mm_raw=mm_raw, inner_raw=inner_raw)
    return HttpResponse(json.dumps(result_list, cls=DjangoJSONEncoder), content_type="application/json")


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

    # 非专属金额
    outer_order_amount = float(outer_raw[0][1] or 0) / 100.0
    mm_order_amount = float(mm_raw[0][1] or 0) / 100.0
    inner_order_amount = float(inner_raw[0][1] or 0) / 100.0

    total_amount = (outer_order_amount + mm_order_amount + inner_order_amount)

    sum_order = outer_order_num + mm_order_num + inner_order_num
    percent_func = lambda num, sum_order: 0 if sum_order == 0 else round(float(num) / sum_order, 3)

    outer_per = percent_func(outer_order_num, sum_order)
    mm_per = percent_func(mm_order_num, sum_order)
    inner_per = percent_func(inner_order_num, sum_order)
    result_lit = [[u"非专属链接", outer_order_num, outer_per, outer_order_amount],
                  [u"代理专属链接", mm_order_num, mm_per, mm_order_amount],
                  [u"内部专属链接", inner_order_num, inner_per, inner_order_amount],
                  [u"订单总数", sum_order, 1, total_amount]]
    return result_lit


"""
2015-08-13
添加到
use shopmgr;
SELECT sum(value)/100 FROM xiaolumm_carrylog WHERE created BETWEEN '2015-07-01' AND '2015-08-01'
 AND log_type = 'rebeta' AND status = 'confirmed' ;      # 订单返利

SELECT sum(value)/100
FROM xiaolumm_carrylog
WHERE created BETWEEN '2015-07-01' AND '2015-08-01'
AND log_type = 'subsidy' AND status = 'confirmed' ;     # 代理补贴

SELECT  count(*),sum(wxorderamount)/100
FROM flashsale_tongji_shopping
WHERE shoptime BETWEEN '2015-07-01' AND '2015-08-01' and status in(0,1) and linkid> 134;

"""


@csrf_exempt
def xlmm_Carry_Log(request):
    """
    计算 某个时间段的小鹿妈妈总的 确定订单返利  待确定订单返利
    """
    content = request.POST
    time_from = content.get("time_from", None)
    time_to = content.get("time_to", None)
    type_value = int(content.get("value", None))

    log_type = judeg_Loge_Type(type_value)

    sql1 = "SELECT log_type ,sum(value)/100 FROM xiaolumm_carrylog WHERE created BETWEEN '{0}' AND '{1}'AND " \
           "log_type in {2} AND status = 'confirmed' AND xlmm>134 GROUP BY log_type;".format(time_from, time_to,
                                                                                             log_type)

    raw = order_num(sql1)
    result_list = carry_Raw_Hander(raw=raw)
    return HttpResponse(json.dumps(result_list, cls=DjangoJSONEncoder), content_type="application/json")


def carry_Raw_Hander(raw=None):
    type_dic = {
        'rebeta': u'订单返利',
        'buy': u'消费支出',
        'click': u'点击兑现',
        'refund': u'退款返现',
        'cashout': u'钱包提现',
        'deposit': u'押金',
        'thousand': u'千元提成',
        'subsidy': u'代理补贴',
        'recruit': u'招募奖金',
        'ordred': u'订单红包'
    }

    result_list = []
    value_all = 0
    all_name = u"总值"
    for i in raw:
        type_name = type_dic[i[0]]
        type_value = i[1]
        type_content = [type_name, type_value]
        result_list.append(type_content)
        value_all += type_value
    result_list.append([all_name, value_all])

    return result_list[::-1]


def judeg_Loge_Type(type_value=None):
    if type_value == 15:
        log_type = ("rebeta", "subsidy", "thousand", "ordred")
    elif type_value == 7:
        log_type = ("rebeta", "subsidy", "thousand")  # 7
    elif type_value == 3:
        log_type = ("rebeta", "subsidy")  # 3
    elif type_value == 1:
        log_type = ("rebeta", "")  # 1
    else:
        log_type = ("rebeta", "")  # 默认返回订单返利
    return log_type
