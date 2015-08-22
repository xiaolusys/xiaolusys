# -*- coding:utf-8 -*-
__author__ = 'yann'
from celery.task import task
from flashsale.pay.models import ShoppingCart, SaleTrade
from shopback.items.models import Product
from django.contrib.auth.models import User as DjangoUser
from shopback.base import log_action, ADDITION, CHANGE
import logging

import json
import urllib,urllib2
from shopback.trades.models import Trade_wuliu
BADU_KD100_URL = "http://www.kuaidiapi.cn/rest"
BAIDU_POST_CODE_EXCHANGE={
                         'YUNDA':'yunda',
                         'STO':'shentong',
                         'EMS':'ems',
                         'ZTO':'zhongtong',
                         'ZJS':'zhaijisong',
                         'SF':'shunfeng',
                         'YTO':'yuantong',
                         'HTKY':'huitongkuaidi',
                         'TTKDEX':'tiantian',
                         'QFKD':'quanfengkuaidi',
                         }
POST_CODE_NAME_MAP = {'YUNDA':u'韵达快递',
                      'STO':u'申通快递',
                      'EMS':u'邮政EMS',
                      'ZTO':u'中通快递',
                      'ZJS':u'宅急送',
                      'SF':u'顺丰速运',
                      'YTO':u'圆通',
                      'HTKY':u'汇通快递',
                      'TTKDEX':u'天天快递',
                      'QFKD':u'全峰快递',
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


import datetime
@task(max_retry=3, default_retry_delay=5)
def task_schedule_cart():
    """
        定时清空购物车中已经超过预留时间和订单中未支付的。
    """
    try:
        djuser, state = DjangoUser.objects.get_or_create(username='systemoa', is_active=True)
        now = datetime.datetime.now()
        all_product_in_cart = ShoppingCart.objects.filter(status=ShoppingCart.NORMAL, remain_time__lte=now)

        for product_in_cart in all_product_in_cart:
            product_in_cart.close_cart()
            log_action(djuser.id, product_in_cart, CHANGE, u'超出预留时间')

        all_trade = SaleTrade.objects.filter(status=SaleTrade.WAIT_BUYER_PAY,
                                             created__lte=datetime.datetime.now() - datetime.timedelta(minutes=20))
        for trade in all_trade:
            try:
                trade.close_trade()
                log_action(djuser.id, trade, CHANGE, u'超出待支付时间')
            except Exception, exc:
                logger = logging.getLogger('django.request')
                logger.error(exc.message, exc_info=True)

    except Exception, exc:
        raise task_schedule_cart.retry(exc=exc)
 
    
#fang  2015-8-21    
@task(max_retry=3, default_retry_delay=5)  
def  SaveWuliu(tid):
    
        # apikey = '47deda738666430bab15306c2878dd3a'     
        apikey='ebd77d3a6ef243c4bf1b1f8610443e27'
    #访问的API代码  
        #uid = '39400'
        uid='40340'
        try:
            trade_info=SaleTrade.objects.get( id=tid )
        except:
            trade_info=SaleTrade.objects.get(tid=tid )

        try:
            exType=trade_info.logistics_company.code
            out_sid=trade_info.out_sid
            if exType  in POST_CODE_NAME_MAP.keys():
                tid=trade_info.tid
                data = {'id':BAIDU_POST_CODE_EXCHANGE.get(exType),'order':out_sid,'key': apikey,'uid': uid}
                req = urllib2.urlopen(BADU_KD100_URL, urllib.urlencode(data),timeout=30)
                content = json.loads(req.read())
                #if content['data'].length=0
                if content['status']==1:
                    wuliu=   Trade_wuliu()
                    wuliu.tid=tid
                    wuliu.status=content['status']
                    wuliu.logistics_company=content['name']
                    wuliu.out_sid=content['order']
                    wuliu.errcode=content['errcode']
                    wuliu.save()
                else:
                    for t in content['data']:
                        wuliu=   Trade_wuliu()
                        wuliu.tid=tid
                        wuliu.status=content['status']
                        wuliu.logistics_company=content['name']
                        wuliu.out_sid=content['order']
                        wuliu.errcode=content['errcode']
                        wuliu.content=t['content']
                        wuliu.time=t['time']
                        wuliu.save()
        except:
            pass




#fang  2015-8-21
@task(max_retry=3, default_retry_delay=5)  
def  SaveWuliu_only01(tid,content):
    """
        用户点击物流信息，进行物流信息存入数据库。
    """
    if content['status']==1:
                    wuliu=   Trade_wuliu()
                    wuliu.tid=tid
                    wuliu.status=content['status']
                    wuliu.logistics_company=content['name']
                    wuliu.out_sid=content['order']
                    wuliu.errcode=content['errcode']
                    wuliu.save()
    else:
                    for t in content['data']:
                        wuliu=   Trade_wuliu()
                        wuliu.tid=tid
                        wuliu.status=content['status']
                        wuliu.logistics_company=content['name']
                        wuliu.out_sid=content['order']
                        wuliu.errcode=content['errcode']
                        wuliu.content=t['content']
                        wuliu.time=t['time']
                        wuliu.save()


#fang  2015-8-22  newVersions
@task(max_retry=3, default_retry_delay=5)  
def  SaveWuliu_only(tid,content):
    """
        用户点击物流信息，进行物流信息存入数据库。
    """
    if content['status']==1:
        try:
            wuliu_info=Trade_wuliu.objects.filter(tid=tid)
            wuliu_info.delete()
            wuliu=   Trade_wuliu()
            wuliu.tid=tid
            wuliu.status=content['status']
            wuliu.logistics_company=content['name']
            wuliu.out_sid=content['order']
            wuliu.errcode=content['errcode']
            wuliu.save()
        except:
            wuliu=   Trade_wuliu()
            wuliu.tid=tid
            wuliu.status=content['status']
            wuliu.logistics_company=content['name']
            wuliu.out_sid=content['order']
            wuliu.errcode=content['errcode']
            wuliu.save()
    else:
        try:
            wuliu_info=Trade_wuliu.objects.filter(tid=tid)
            wuliu_info.delete()
            for t in content['data']:
                wuliu=   Trade_wuliu()
                wuliu.tid=tid
                wuliu.status=content['status']
                wuliu.logistics_company=content['name']
                wuliu.out_sid=content['order']
                wuliu.errcode=content['errcode']
                wuliu.content=t['content']
                wuliu.time=t['time']
                wuliu.save()
        except:
            for t in content['data']:
                wuliu=   Trade_wuliu()
                wuliu.tid=tid
                wuliu.status=content['status']
                wuliu.logistics_company=content['name']
                wuliu.out_sid=content['order']
                wuliu.errcode=content['errcode']
                wuliu.content=t['content']
                wuliu.time=t['time']
                wuliu.save()
