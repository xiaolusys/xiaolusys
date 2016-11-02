# -*- coding:utf-8 -*-

from shopapp.zhongtong.ztjiekou import zhongtong
from shopapp.zhongtong import code

import views
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from xhtml2pdf import pisa
from .models import ZTOOrderList


# html转pdf
def genHtmlPdf(file_path, html_text):
    resultFile = open(file_path, 'w+b')

    # convert HTML to PDF
    pisaStatus = pisa.CreatePDF(
        html_text,
        dest=resultFile)

    # close output file
    resultFile.close()


# 打印
def zprint(request, out_sid):
    m = ZTOOrderList.objects.filter(out_sid=out_sid)

    mt = m[0]

    data = "{'sendcity':'上海,上海市,松江区','receivercity':'" + mt.receiver_state + "," + mt.receiver_city + "," + mt.receiver_district + "'}"

    # 链接中通接口
    ls = zhongtong.handle_demon(data, "order.marke")

    # 获取物流单号，生成条形码
    out_sid = mt.out_sid
    imgbase64 = code.createbar_code128(out_sid)

    # 生成二维码
    imgbase = code.two_dimension_code(out_sid)

    date_time = mt.consign_time.strftime('%Y-%m-%d')
    shuju = {'mt': mt, 'ls': ls, 'date_time': date_time, 'imgbase64': imgbase64, 'imgbase': imgbase}

    # 打印记录
    views.printrecord(request, mt)

    # 更改订单列表打印状态(已打印)
    ol = ZTOOrderList.objects.get(yid=mt.yid)
    ol.status = 0
    ol.save()

    return shuju


def lianda(request, result_dict):
    # 生成HTML
    invoice_html = render_to_string('zto_bill.html', {'result_dict': result_dict})
    # 定义pdf名称
    file_name = "zto_bill.pdf"
    # html转pdf
    genHtmlPdf(file_name, invoice_html.encode('utf8'))


# 批量打印
@csrf_exempt
def ztoprint(request):
    queryse = [{'out_sid': '728105650184', 'test': '728105650184'}, {'out_sid': '718850489884', 'test': '728105650184'}]

    result_dict = {}
    for v in queryse:
        shuju = zprint(request, v['out_sid'])

        result_dict[v['out_sid']] = shuju

    lianda(request, result_dict)

    return HttpResponse("OK")
