#-*- coding:utf-8 -*-

from django.template.loader import render_to_string
from django.http import HttpResponse
import time
import datetime
import views
from shopmanager.shopapp.zhongtong.ztjiekou import zhongtong
from xhtml2pdf import pisa
from shopmanager.shopapp.zhongtong import code
from shopback.trades.models import MergeTrade
from .models import OrderList


#html转pdf
def genHtmlPdf(file_path,html_text):

    resultFile = open(file_path, 'w+b')

    # convert HTML to PDF
    pisaStatus = pisa.CreatePDF(
        html_text,
        dest=resultFile)

    # close output file
    resultFile.close()

#打印
def runprint(request,out_sid):

    m = OrderList.objects.filter(out_sid=out_sid)

    mt = m[0]

    data ="{'sendcity':'上海,上海市,松江区','receivercity':'"+mt.receiver_state+","+mt.receiver_city+","+mt.receiver_district+"'}"

    #链接中通接口
    ls = zhongtong.handle_demon(data,"order.marke")

    #获取物流单号，生成二维码
    out_sid   = mt.out_sid
    imgbase64 = code.createbar_code128(out_sid)

    date_time = mt.consign_time.strftime('%Y-%m-%d')
    invoice_html = render_to_string('timi.html', {'mt': mt, 'ls': ls,'date_time':date_time,'imgbase64': imgbase64})
    print "debug =========:", invoice_html
    print "当前时间：：",time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

    file_name = "%s.pdf"%out_sid
    #html转pdf
    genHtmlPdf(file_name, invoice_html.encode('utf8'))

    #打印记录
    views.printrecord(request,mt)

    #更改订单列表打印状态(YES)
    ol = OrderList.objects.get(yid=mt.yid)
    ol.status = 0
    ol.save()
    # mgt = MergeTrade.objects.get(tid=mt.yid)
    # mgt.operator   = request.user.username
    # mgt.qrcode_msg = "已打印"
    # mgt.save()



    return HttpResponse('打印成功！')
    #return render(request,open("../%s.pdf"test))
