# -*- coding:utf-8 -*-
__author__ = 'yann'
from celery.task import task
from flashsale.pay.models import ShoppingCart, SaleTrade


@task(max_retry=3, default_retry_delay=5)
def task_off_the_shelf(product_id=None):
    try:
        ShoppingCart.objects.filter(item_id=product_id).update(status=u"1")
        SaleTrade.objects.filter(sale_orders__item_id=product_id).update(status=7)
    except Exception, exc:
        raise task_off_the_shelf.retry(exc=exc)
