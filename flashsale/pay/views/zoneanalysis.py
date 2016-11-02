# coding=utf-8
from django.db import connection, transaction
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
import datetime

"""
 统计购买用户各地区分布比例（按省，直辖市统计）按月份统计
# 按省份
    # 特卖平台
    select receiver_state,count(id) from flashsale_trade where created  between '2015-03-01' and '2015-04-01'  group by receiver_state;
    # 微信平台
    select receiver_province,count(order_id) from shop_weixin_order  where order_create_time  between '2015-03-01' and '2015-04-01' group by receiver_province  ;


# 按城市
    # 特卖平台
    select receiver_city,count(id) from flashsale_trade group by receiver_city;
    # 微信平台
    select receiver_city,count(order_id) from shop_weixin_order group by receiver_city;
"""


@csrf_exempt
def by_zone_Province(request):
    content = request.POST
    time_from = content.get("time_from", None)
    time_to = content.get("time_to", None)

    sql1 = "select receiver_state,count(id) from flashsale_trade where created " \
           " between '{0}' and '{1}'  group by receiver_state ;".format(time_from, time_to)
    sql2 = "select receiver_province,count(order_id) from shop_weixin_order  where order_create_time " \
           " between '{0}' and '{1}' group by receiver_province  ;".format(time_from, time_to)
    pay_raw = pay_trade(sql1)
    weixin_raw = weixin_trade(sql2)

    raw = province_raw_handler(pay_raw=pay_raw, weixin_raw=weixin_raw)
    return HttpResponse(json.dumps(raw, cls=DjangoJSONEncoder), content_type="application/json")


@csrf_exempt
def by_zone_City(request):
    content = request.POST
    time_from = content.get("time_from", None)
    time_to = content.get("time_to", None)
    sql1 = "select receiver_city,count(id) from flashsale_trade  where created " \
           "between '{0}' and '{1}'  group by receiver_city ;".format(time_from, time_to)
    sql2 = "select receiver_city,count(order_id) from shop_weixin_order  where order_create_time " \
           " between '{0}' and '{1}'  group by receiver_city;".format(time_from, time_to)
    pay_raw = pay_trade(sql1)
    weixin_raw = weixin_trade(sql2)

    raw = city_raw_handler(pay_raw=pay_raw, weixin_raw=weixin_raw)
    return HttpResponse(json.dumps(raw, cls=DjangoJSONEncoder), content_type="application/json")


def show_Zone_Page(request):
    date_today = datetime.datetime.today()
    today = date_today.strftime("%Y-%m-%d")
    return render_to_response("pay/zone_analysis/zone_analysis.html", {"today": today},
                              context_instance=RequestContext(request))


def pay_trade(sql=None):
    """
    查询出  特卖平台  的地域订单数据源 并返回
    """
    if sql:
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        cursor.close()
        return raw
    else:
        return


def weixin_trade(sql=None):
    """
    查询出  微信平台  的地域订单数据源 并返回
    """
    if sql:
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        cursor.close()
        return raw
    else:
        return


def province_raw_handler(pay_raw=None, weixin_raw=None):
    """
    处理sql的raw 两个类别的raw 结果(两列，键-值)
    返回 合并后的元组列表
    """
    pro_s = set()
    pay_raw_dic = {}
    pay_sum_num = 0
    for i in pay_raw:
        province = i[0][0:2]
        if province == "":
            continue
        num = i[1]
        pay_sum_num += num
        pay_raw_dic[province] = num
        pro_s.add(province)  # 省份集合

    weixin_raw_dic = {}
    weixin_sum_num = 0
    for j in weixin_raw:
        province = j[0][0:2]  # 截取前面两个字符来核算 省份
        if province == "":
            continue
        num = j[1]
        weixin_sum_num += num
        weixin_raw_dic[province] = num
        pro_s.add(province)  # 省份集合
    total_num = pay_sum_num + weixin_sum_num

    sum_lit = []
    for s in pro_s:  # 寻找存在的KEY求和
        x = pay_raw_dic[s] if s in pay_raw_dic else 0
        y = weixin_raw_dic[s] if s in weixin_raw_dic else 0
        sum_num = x + y
        sum_lit.append((s, sum_num))

    sum_lit = sorted(sum_lit, key=lambda s: s[1])
    sum_lit.append((u"总单数量", total_num))
    return sum_lit[::-1]


def city_raw_handler(pay_raw=None, weixin_raw=None):
    """
    处理sql的raw 两个类别的raw 结果(两列，键-值)
    返回 合并后的元组列表
    """
    pro_s = set()
    pay_raw_dic = {}
    pay_sum_num = 0
    for i in pay_raw:
        province = i[0][0:3]
        if province == "":
            continue
        num = i[1]
        pay_sum_num += num
        pay_raw_dic[province] = num
        pro_s.add(province)  # 省份集合
    weixin_raw_dic = {}
    weixin_sum_num = 0
    for j in weixin_raw:
        province = j[0][0:3]  # 截取前面两个字符来核算 省份
        if province == "":
            continue
        num = j[1]
        weixin_sum_num += num
        weixin_raw_dic[province] = num
        pro_s.add(province)  # 省份集合

    total_num = pay_sum_num + weixin_sum_num

    sum_lit = []
    for s in pro_s:  # 寻找存在的KEY求和
        x = pay_raw_dic[s] if s in pay_raw_dic else 0
        y = weixin_raw_dic[s] if s in weixin_raw_dic else 0
        sum_num = x + y
        sum_lit.append((s, sum_num))
    sum_lit = sorted(sum_lit, key=lambda s: s[1])
    sum_lit.append((u"总单数量", total_num))
    return sum_lit[::-1]
