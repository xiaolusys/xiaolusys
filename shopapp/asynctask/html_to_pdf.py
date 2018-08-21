# -*- coding:utf-8 -*-

import time

from django.template.loader import render_to_string
from shopapp.zhongtong import code
from xhtml2pdf import pisa
from .models import PrintAsyncTaskModel


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
def runprint(request, out_sid):
    p = PrintAsyncTaskModel.objects.filter(out_sid=out_sid)

    pt = p[0]

    # data ="{'sendcity':'上海,上海市,松江区','receivercity':'"+pt.receiver_state+","+pt.receiver_city+","+pt.receiver_district+"'}"
    #
    # #链接韵达接口
    # ls = yunda.handle_demon(data,"order.marke")

    # 获取物流单号，生成二维码
    out_sid = pt.out_sid
    imgbase64 = code.createbar_code128(out_sid)

    # 生成二维码
    imgbase = code.two_dimension_code(out_sid)

    date_time = pt.consign_time.strftime('%Y-%m-%d')
    shuju = {'pt': pt, 'date_time': date_time, 'imgbase64': imgbase64, 'imgbase': imgbase}

    return shuju


def lianda(request, result_dict):
    print type(result_dict), result_dict
    invoice_html = render_to_string('yunda_bill.html', {'result_dict': result_dict})
    # print "debug =========:", invoice_html
    print "当前时间：：", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

    file_name = "yunda_bill.pdf"
    # html转pdf
    genHtmlPdf(file_name, invoice_html.encode('utf8'))
