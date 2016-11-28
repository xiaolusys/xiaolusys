# coding=utf-8
from __future__ import unicode_literals,absolute_import

from .. import supplier_sku
from django.http import HttpResponse
import json
from django.shortcuts import render
import datetime

import xlsxwriter
from cStringIO import StringIO
from core.utils.csvutils import CSVUnicodeWriter




def get_supplier_sku(request,salesupplier_id):
    supplier_sku_data = supplier_sku.get_supplier_sku(salesupplier_id)
    start_time = request.GET.get("start_time")
    end_time = request.GET.get("end_time")

    if start_time and end_time:
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d").date()
        end_time = datetime.datetime.strptime(end_time, "%Y-%m-%d").date()
        supplier_sku_data = supplier_sku.get_supplier_sku_by_time(salesupplier_id,start_time,end_time)
        print supplier_sku_data
        return render(request,"dinghuo/supplier_sku.html",{'supplier_sku': supplier_sku_data,"start_time":start_time,"end_time":end_time})

    return render(request,"dinghuo/supplier_sku.html",{'supplier_sku': supplier_sku_data})

    # return HttpResponse(json.dumps(supplier_sku_data), status=200,content_type='application/json')

def get_supplier_sku_excel(request,salesupplier_id):
    excel_format = request.GET.get('fo', '')
    start_time = request.GET.get("start_time",None)
    end_time = request.GET.get("end_time",None)
    if start_time and end_time:
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d").date()
        end_time = datetime.datetime.strptime(end_time, "%Y-%m-%d").date()
        supplier_sku_data = supplier_sku.get_supplier_sku_by_time(salesupplier_id,start_time,end_time)
    else:
        supplier_sku_data = supplier_sku.get_supplier_sku(salesupplier_id)
    columns = ["ID",'供应商名字','产品名称','产品规格','产品外部编码','SKU','到仓数量','最早一件采购到仓时间','最晚一件采购到仓时间']
    items = list()
    for sku in supplier_sku_data:
        print sku['outer_id']
        items.append([str(sku['salesupplier_id']),str(sku["supplier_name"]),str(sku['product_name']),str(sku['product_chicun']),
                      str(sku['outer_id']),str(sku['chichu_id']),str(sku['arrival_quantity__sum']),str(sku['arrival_time__min']),str(sku['arrival_time__max'])])


        # 前段懒得美化了raise exceptions.ValidationError(make_response(e0.message))
    items = [columns] + items
    buff = StringIO()
    is_windows = request.META['HTTP_USER_AGENT'].lower().find(
        'windows') > -1
    writer = CSVUnicodeWriter(buff,
                              encoding=is_windows and 'gbk' or 'utf-8')
    writer.writerows(items)
    response = HttpResponse(buff.getvalue(),
                            content_type='application/octet-stream')
    response[
        'Content-Disposition'] = 'attachment;filename=packagedetail-%s.csv' % "zuile"
    return response
    # supplier_sku_data = supplier_sku.get_supplier_sku(salesupplier_id)
    # buff = StringIO()
    # workbook = xlsxwriter.Workbook(buff)
    # worksheet = workbook.add_worksheet()
    # bold_format = workbook.add_format({"bold": True})
    # worksheet.set_column('A:A', 18)
    # worksheet.set_column('B:B', 30)
    # worksheet.set_column('C:C', 30)
    # worksheet.set_column('D:D', 30)
    # worksheet.set_column('E:E', 30)
    # worksheet.set_column('F:F', 30)
    # worksheet.set_column('G:G', 30)
    # worksheet.set_column('H:H', 30)
    # worksheet.set_column('I:I', 30)
    # worksheet.set_column('J:J', 30)
    # worksheet.set_column('K:K', 30)
    # worksheet.write('A6', 'ID', bold_format)
    # worksheet.write('B6', u'供应商名字', bold_format)
    # worksheet.write('C6', u'产品名称', bold_format)
    # worksheet.write('D6', u'产品规格', bold_format)
    # worksheet.write('E6', u'产品外部编码', bold_format)
    # worksheet.write('F6', 'SKU', bold_format)
    # worksheet.write('G6', u'到仓数量', bold_format)
    # worksheet.write('H6', u'最早一件采购到仓时间', bold_format)
    # worksheet.write('I6', u'最晚一件采购到仓时间', bold_format)
    # worksheet.write('J6', u'账单状态', bold_format)
    # worksheet.write('K6', u'备注', bold_format)
    # row = 7
    # for sku in supplier_sku_data:
    #     worksheet.write(row, 0, sku['supplier_name'])
    #     worksheet.write(row, 1, sku['product_name'])
    #     worksheet.write(row, 2, sku['product_chicun'])
    #     worksheet.write(row, 3, sku['outer_id'])
    #     worksheet.write(row, 4, sku['chichu_id'])
    #     worksheet.write(row, 5, sku['arrival_quantity__sum'])
    #     worksheet.write(row, 6, sku['arrival_time__min'])
    #     worksheet.write(row, 7, sku['arrival_time__max'])
    #     worksheet.write(row, 8, 123)
    #     worksheet.write(row, 9, 123)
    #     worksheet.write(row, 10, 123)
    #     row += 1
    # workbook.close()
    # filename = '%s-%s.xlsx' % (salesupplier_id, supplier_sku_data[0]['supplier_name'])
    # response = HttpResponse(
    #     buff.getvalue(),
    #     content_type=
    #     'application/octet-stream')
    # response['Content-Disposition'] = 'attachment;filename=%s' % filename
    # return response







