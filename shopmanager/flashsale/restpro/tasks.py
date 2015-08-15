# -*- coding:utf-8 -*-
__author__ = 'yann'
from celery.task import task
from flashsale.pay.models import ShoppingCart, SaleTrade
from shopback.items.models import Product
from django.contrib.auth.models import User as DjangoUser
from shopback.base import log_action, ADDITION, CHANGE


@task(max_retry=3, default_retry_delay=5)
def task_off_the_shelf(product_id=None):
    """
        如果有传入商品的id，就执行一个
        否则定时执行，找出购物车和订单中的下架的商品，并且进行处理
    """
    try:
        djuser, state = DjangoUser.objects.get_or_create(username='systemoa', is_active=True)
        if product_id is None:
            all_product_in_cart = ShoppingCart.objects.filter(status=ShoppingCart.NORMAL)
            for product_in_cart in all_product_in_cart:
                product_a = Product.objects.filter(id=product_in_cart.item_id)
                if product_a.count() > 0 and product_a[0].shelf_status == Product.DOWN_SHELF:
                    product_in_cart.close_cart()
                    log_action(djuser.id, product_in_cart, CHANGE, u'下架后更新')

            all_trade = SaleTrade.objects.filter(status=SaleTrade.WAIT_BUYER_PAY)
            for trade in all_trade:
                all_order = trade.sale_orders.all()
                for order in all_order:
                    product_b = Product.objects.filter(outer_id=order.outer_id)
                    if product_b.count() > 0 \
                            and product_b[0].shelf_status == Product.DOWN_SHELF \
                            and trade.status == SaleTrade.WAIT_BUYER_PAY:
                        trade.close_trade()
                        log_action(djuser.id, trade, CHANGE, u'系统更新待付款状态到交易关闭')

        else:
            all_cart = ShoppingCart.objects.filter(item_id=product_id, status=ShoppingCart.NORMAL)
            for cart in all_cart:
                cart.close_cart()
                log_action(djuser.id, cart, CHANGE, u'下架后更新')

            all_trade = SaleTrade.objects.filter(sale_orders__item_id=product_id, status=SaleTrade.WAIT_BUYER_PAY)
            for trade in all_trade:
                trade.close_trade()
                log_action(djuser.id, trade, CHANGE, u'系统更新待付款状态到交易关闭')

    except Exception, exc:
        raise task_off_the_shelf.retry(exc=exc)
