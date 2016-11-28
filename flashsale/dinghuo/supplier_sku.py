# coding=utf-8

from __future__ import unicode_literals,absolute_import

import os,sys,django
sys.path.append("/home/fpcnm/myProjects/xiaoluMM4/xiaolusys/shopmanager/")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")
django.setup()

from flashsale.dinghuo.models import OrderDetail,OrderList
from django.db.models import Count,Min,Max,Sum
from supplychain.supplier.models import  SaleSupplier
import datetime



def get_supplier_sku(salesupplier_id):   #返回给定供应商的所有历史购买sku数
    sale_supplier = SaleSupplier.objects.filter(id=int(salesupplier_id)).first()
    if sale_supplier:
        order_list = OrderList.objects.filter(supplier=sale_supplier)
        order_detail = OrderDetail.objects.filter(orderlist__in=order_list)
        sku_count = order_detail.values("chichu_id","outer_id","product_name","product_chicun").annotate(Sum("buy_quantity"),Sum("arrival_quantity"),Min("arrival_time"),Max('arrival_time'))
        for i in sku_count:
            i['arrival_time__max'] = str(i['arrival_time__max'])
            i['arrival_time__min'] = str(i['arrival_time__min'])
            i['supplier_name'] = sale_supplier.supplier_name
            i['salesupplier_id'] = salesupplier_id
        sku_count = list(sku_count)
        return sku_count

def get_supplier_sku_by_time(salesupplier_id, start_time, end_time):
    print start_time,end_time
    sale_supplier = SaleSupplier.objects.filter(id=int(salesupplier_id)).first()
    if sale_supplier:
        order_list = OrderList.objects.filter(supplier=sale_supplier)
        order_detail = OrderDetail.objects.filter(orderlist__in=order_list)
        sku_count = order_detail.values("chichu_id","outer_id","product_name","product_chicun").annotate(Sum("arrival_quantity"),Min("arrival_time"),Max('arrival_time'))
        sku_count = list(sku_count)
        sku_count_temp = list()
        for i in sku_count:
            if i['arrival_time__min'] and i['arrival_time__max']:
                i_start_time = datetime.datetime.strptime(str(i['arrival_time__min']), "%Y-%m-%d %H:%M:%S").date()
                i_end_time = datetime.datetime.strptime(str(i['arrival_time__max']), "%Y-%m-%d %H:%M:%S").date()
            if i_end_time<end_time and i_start_time>start_time:
                sku_count_temp.append(i)
        sku_count = sku_count_temp
        for i in sku_count:
            i['arrival_time__max'] = str(i['arrival_time__max'])
            i['arrival_time__min'] = str(i['arrival_time__min'])
            i['supplier_name'] = sale_supplier.supplier_name
            i['salesupplier_id'] = salesupplier_id
        sku_count = list(sku_count)
        print sku_count
        return sku_count


if __name__ == '__main__':
    print get_supplier_sku(29463)
