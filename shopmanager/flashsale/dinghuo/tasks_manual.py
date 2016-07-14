# -*- coding:utf-8 -*-
import datetime
from celery.task import task
from shopback.items.models import Product, ProductSku
from flashsale.dinghuo.models import OrderDetail, OrderList

from supplychain.supplier.models import SaleProduct
from core.options import log_action, CHANGE, get_systemoa_user


@task()
def task_dinghuo_supplier():
    """将供应商名字写入订货表"""
    since_time = datetime.date(2015, 9, 20)
    all_dinghuo = OrderList.objects.filter(created__gt=since_time, supplier_shop="")
    for one_dinghuo in all_dinghuo:
        all_product = [detail.product_id for detail in one_dinghuo.order_list.all()]
        supplier = ""
        for one_product in all_product:
            try:
                a = Product.objects.get(id=one_product)
                sale_product = SaleProduct.objects.get(id=a.sale_product)
                supplier = sale_product.sale_supplier.supplier_name
                break
            except:
                continue
        if supplier != "":
            one_dinghuo.supplier_shop = supplier
            one_dinghuo.save()
            log_action(get_systemoa_user().id, one_dinghuo, CHANGE, u'修改供应商')




