# -*- coding:utf-8 -*-
__author__ = 'yann'
from celery.task import task
from flashsale.pay.models import ShoppingCart, SaleTrade
from shopback.items.models import Product
from django.contrib.auth.models import User as DjangoUser
from core.options import log_action, ADDITION, CHANGE
import logging

import json
import urllib, urllib2
from shopback.trades.models import TradeWuliu

BADU_KD100_URL = "http://www.kuaidiapi.cn/rest"
BAIDU_POST_CODE_EXCHANGE = {
    'YUNDA': 'yunda',
    'STO': 'shentong',
    'EMS': 'ems',
    'ZTO': 'zhongtong',
    'ZJS': 'zhaijisong',
    'SF': 'shunfeng',
    'YTO': 'yuantong',
    'HTKY': 'huitongkuaidi',
    'TTKDEX': 'tiantian',
    'QFKD': 'quanfengkuaidi',
}
POST_CODE_NAME_MAP = {'YUNDA': u'韵达快递',
                      'STO': u'申通快递',
                      'EMS': u'邮政EMS',
                      'ZTO': u'中通快递',
                      'ZJS': u'宅急送',
                      'SF': u'顺丰速运',
                      'YTO': u'圆通',
                      'HTKY': u'汇通快递',
                      'TTKDEX': u'天天快递',
                      'QFKD': u'全峰快递',
                      }


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
                        try:
                            trade.close_trade()
                            log_action(djuser.id, trade, CHANGE, u'系统更新待付款状态到交易关闭')
                        except Exception, exc:
                            logger = logging.getLogger('django.request')
                            logger.error(exc.message, exc_info=True)

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


from common.cachelock import cache_lock
import datetime


@cache_lock(cache_time=60 * 60)
def close_timeout_carts_and_orders():
    djuser, state = DjangoUser.objects.get_or_create(username='systemoa', is_active=True)
    now = datetime.datetime.now()
    all_product_in_cart = ShoppingCart.objects.filter(status=ShoppingCart.NORMAL, remain_time__lte=now)

    for product_in_cart in all_product_in_cart:
        product_in_cart.close_cart()
        log_action(djuser.id, product_in_cart, CHANGE, u'超出预留时间')

    all_trade = SaleTrade.objects.filter(status=SaleTrade.WAIT_BUYER_PAY)
    for trade in all_trade:
        if trade.is_payable():
            continue
        try:
            trade.close_trade()
            log_action(djuser.id, trade, CHANGE, u'超出待支付时间')
        except Exception, exc:
            logger = logging.getLogger('django.request')
            logger.error(exc.message, exc_info=True)


@task()
def task_schedule_cart():
    """
        定时清空购物车中已经超过预留时间和订单中未支付的。
    """
    close_timeout_carts_and_orders()


@task(max_retry=3, default_retry_delay=5)
def SaveWuliu_only(tid, content):
    """
        用户点击物流信息，进行物流信息存入数据库。
    """
    wulius = TradeWuliu.objects.filter(tid=tid).order_by("-time")
    datalen = len(content['data'])
    data = content['data']
    alread_count = wulius.count()
    if alread_count >= datalen:  # 已有记录条数大于等于接口给予条数只是更新状态到最后一条记录中
        if wulius.exists():
            wuliu = wulius[0]
            wuliu.status = int(content['status'])
            wuliu.save()
    else:  # 如果接口数据大于已经存储的条数　则创建　多出来的条目　
        if wulius.exists():
            wulius.delete()  # 删除旧数据
        for da in data:  # 保存新数据
            TradeWuliu.objects.create(tid=tid, status=content['status'], logistics_company=content['name'],
                                      out_sid=content['order'], errcode=content['errcode'],
                                      content=da['content'], time=da['time'])


from flashsale.pay.models_shops import CustomerShops, CuShopPros
from views_cushops import save_pro_info
import logging

logger = logging.getLogger(__name__)


@task()
def prods_position_handler():
    """ 初始化店铺产品的信息 """
    shops = CustomerShops.objects.all()
    for shop in shops:
        shop_pros = CuShopPros.objects.filter(shop=shop.id).order_by('-created')  # 指定店铺的所有产品按照时间逆序
        pros_count = shop_pros.count()  # 计算该店铺产品的数量
        for pro in shop_pros:
            pro.position = pros_count  # 初始化商品的位置号
            pro.save()
            pros_count = pros_count - 1
            shop = pro.get_customer()
            customer = shop.get_customer()
            try:
                save_pro_info(product=pro.product, user=customer.user)
            except Exception, exc:
                logger.error(exc.message)
    up_pro_ids = Product.objects.filter(status=Product.NORMAL, shelf_status=Product.UP_SHELF).values('id')
    cu_pros = CuShopPros.objects.all().exclude(id__in=up_pro_ids)
    cu_pros.update(pro_status=CuShopPros.DOWN_SHELF)
