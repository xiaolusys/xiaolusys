# coding=utf-8
"""
    功能：质量问题的退货 要追踪到买手 以便 了解渠道问题
"""
from django.db import connection
from django.shortcuts import render
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
import datetime


@csrf_exempt
def tracert_Page_Show(request):
    date_today = datetime.datetime.today()
    today = date_today.strftime("%Y-%m-%d")
    third_day = date_today - datetime.timedelta(days=30)  # 默认30天
    third_day_p = third_day.strftime("%Y-%m-%d")
    return render(
        request,
        "refunds/refund_pro_quality_tracert.html",
        {"third_day_p": third_day_p, "today": today},
    )


@csrf_exempt
def tracert_Data_Collect(request):
    content = request.POST
    time_from = content.get("time_from", None)
    time_to = content.get("time_to", None)
    reason = 3  # 质量问题
    sql1 = "select title,outer_id ,sum(num) from shop_refunds_product where reason={2} and created " \
           " between '{0}' and '{1}' group by outer_id;".format(time_from, time_to, reason)
    raw = raw_db(sql=sql1)
    result_list = refund_Raw_Handler(raw=raw)
    return HttpResponse(json.dumps(result_list, cls=DjangoJSONEncoder), content_type="application/json")


def raw_db(sql=None):
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


def refund_Raw_Handler(raw=None):
    result_list = []
    for r in raw:
        outer_id = r[1]
        char_raw = find_Sale_Charge(outer_id=outer_id)
        pro_li = [char_raw[0][0], char_raw[0][1], r[0], r[1], r[2]]
        # 图片链接  采购员  标题  编码  退货数量
        result_list.append(pro_li)
    return result_list


def find_Sale_Charge(outer_id=None):
    sql2 = "select pic_path,sale_charger from shop_items_product where outer_id='{0}';".format(outer_id)
    raw = raw_db(sql=sql2)
    if raw:
        return raw
    else:
        raw = ((u'', u''),)
        return raw
