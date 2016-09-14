# -*- coding:utf-8 -*-
__author__ = 'yann'
import json
import urllib, urllib2

from celery.task import task
from django.contrib.auth.models import User as DjangoUser
from django.db.models import F
from core.options import log_action, ADDITION, CHANGE
from flashsale.pay.models import ShoppingCart, SaleTrade, CustomerShops, CuShopPros
from shopback.items.models import Product, ProductSkuStats
from flashsale.pay.models import SaleRefund
from shopback.trades.models import TradeWuliu, PackageSkuItem,ReturnWuLiu
from flashsale.restpro.utils import save_pro_info
from flashsale.restpro.kdn_wuliu_extra import kdn_subscription
import logging
logger = logging.getLogger(__name__)


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


@task(max_retries=3, default_retry_delay=5)
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


def close_timeout_carts_and_orders_reset_cart_num(skus=[]):
    """
        1/定时处理，对各sku清理超时shoppingcart
        2/购物车检查
        3/进行购物车检查
        4移出购物车
    """
    from shopback.items.models import ProductSkuStats
    from flashsale.pay.tasks_stats import task_shoppingcart_update_productskustats_shoppingcart_num
    djuser, state = DjangoUser.objects.get_or_create(username='systemoa', is_active=True)
    now = datetime.datetime.now()
    extend_skus = []
    if not skus:
        all_product_in_cart = ShoppingCart.objects.filter(status=ShoppingCart.NORMAL, remain_time__lte=now)
        skus = [c['sku_id'] for c in all_product_in_cart.values('sku_id').distinct()]
        extend_skus = [p['sku_id'] for p in ProductSkuStats.objects.filter(shoppingcart_num__gt=0).exclude(sku_id__in=skus).values('sku_id')]
    else:
        all_product_in_cart = ShoppingCart.objects.filter(sku_id__in=skus, status=ShoppingCart.NORMAL, remain_time__lte=now)
    all_product_in_cart.update(status=ShoppingCart.CANCEL)
    for sku in skus + extend_skus:
        task_shoppingcart_update_productskustats_shoppingcart_num(sku)
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
def task_add_shoppingcart_num(instance):
    stat = ProductSkuStats.get_by_sku(instance.sku_id)
    ProductSkuStats.objects.filter(sku_id=stat.sku_id).update(shoppingcart_num=F('shoppingcart_num')+instance.num)
    return close_timeout_carts_and_orders_reset_cart_num([instance.sku_id])


@task()
def task_schedule_cart():
    """
        定时清空购物车中已经超过预留时间和订单中未支付的。

    """
    close_timeout_carts_and_orders_reset_cart_num()


BADU_KD100_URL = "http://www.kuaidiapi.cn/rest"  # 访问第三方接口
apikey = '47deda738666430bab15306c2878dd3a'
uid = '39400'
default_post = 'yunda'

BAIDU_POST_CODE_EXCHANGE = {
    'YUNDA': 'yunda', 'YUNDA_QR': 'yunda', 'STO': 'shentong', 'EMS': 'ems', 'ZTO': 'zhongtong', 'ZJS': 'zhaijisong',
    'SF': 'shunfeng', 'YTO': 'yuantong', 'HTKY': 'huitongkuaidi', 'TTKDEX': 'tiantian',
    'QFKD': 'quanfengkuaidi',
}

@task()
def get_third_apidata(trade):
    """ 访问第三方api 获取物流参数 并保存到本地数据库　"""
    tid = trade.tid
    # 快递编码(快递公司编码)
    exType = trade.logistics_company.code if trade.logistics_company is not None else default_post
    data = {'id': BAIDU_POST_CODE_EXCHANGE.get(exType), 'order': trade.out_sid, 'key': apikey,
            'uid': uid}
    req = urllib2.urlopen(BADU_KD100_URL, urllib.urlencode(data), timeout=30)
    content = json.loads(req.read())
    SaveWuliu_only.delay(tid, content)  # 异步任务，存储物 流信息到数据库
    return

@task()
def get_third_apidata_by_packetid(packetid, company_code):
    """ 使用包裹id访问第三方api 获取物流参数 并保存到本地数据库　"""

    # 快递编码(快递公司编码)
    exType = company_code if company_code is not None else default_post
    data = {'id': BAIDU_POST_CODE_EXCHANGE.get(exType), 'order': packetid, 'key': apikey,
            'uid': uid}
    req = urllib2.urlopen(BADU_KD100_URL, urllib.urlencode(data), timeout=30)
    content = json.loads(req.read())
    SaveWuliu_by_packetid.delay(packetid, content)  # 异步任务，存储物 流信息到数据库
    return

@task()
def get_third_apidata_by_packetid_return(rid,packetid, company_code):   #by huazi
    """ 使用包裹id访问第三方api 获取退货物流参数 并保存到本地数据库　"""

    # 快递编码(快递公司编码)
    # exType = company_code if company_code is not None else default_post
    data = {'id': company_code, 'order': packetid, 'key': apikey,
            'uid': uid}
    req = urllib2.urlopen(BADU_KD100_URL, urllib.urlencode(data), timeout=30)
    content = json.loads(req.read())
    # logger.warn("看看物流数据")
    # logger.warn(content)
    SaveReturnWuliu_by_packetid.delay(rid,packetid,content)
    return

@task()
def kdn_sub(rid, expName, expNo):
    logging.warn(expNo)
    logging.warn("开始订阅了")
    exp_info = {"expName": expName, "expNo": expNo}
    kdn_subscription(**exp_info)


@task(max_retries=3, default_retry_delay=5)
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


@task(max_retries=3, default_retry_delay=5)
def SaveWuliu_by_packetid(packetid, content):
    """
        用户点击物流信息，进行物流信息存入数据库。
    """
    wulius = TradeWuliu.objects.filter(out_sid=packetid).order_by("-time")
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
            TradeWuliu.objects.create(tid='', status=content['status'], logistics_company=content['name'],
                                      out_sid=content['order'], errcode=content['errcode'],
                                      content=da['content'], time=da['time'])

@task(max_retries=3, default_retry_delay=5)  #by huazi
def SaveReturnWuliu_by_packetid(rid,packetid, content):
    """
        用户点击物流信息，进行物流信息存入数据库。
    """
    # logger.warn("开始执行准备写入数据库的函数了")
    wulius = ReturnWuLiu.objects.filter(out_sid=packetid).order_by("-time")
    datalen = len(content['data'])
    data = content['data']
    alread_count = wulius.count()
    if alread_count >= datalen:  # 已有记录条数大于等于接口给予条数只是更新状态到最后一条记录中
        if wulius.exists():
            wuliu = wulius[0]
            wuliu.status = int(content['status'])
            wuliu.save()
            # print "写入成功"
    else:  # 如果接口数据大于已经存储的条数　则创建　多出来的条目　
        if wulius.exists():
            wulius.delete()  # 删除旧数据
        for da in data:  # 保存新数据
            ReturnWuLiu.objects.create(tid='', rid=rid,status=content['status'], logistics_company=content['name'],
                                      out_sid=content['order'], errcode=content['errcode'],
                                      content=da['content'], time=da['time'])
            # logger.warn("数据库里面有记录更新记录写入成功")


#
@task()
def update_all_logistics():
    from flashsale.restpro.v1.views_wuliu_new import get_third_apidata_by_packetid
    sale_trades = SaleTrade.objects.filter(status__in= [SaleTrade.WAIT_SELLER_SEND_GOODS,
                                                      SaleTrade.WAIT_BUYER_CONFIRM_GOODS])
    #print 'update_all_logistics %d'%(sale_trades.count())
    num = 0
    for t in sale_trades:
        #print 'get trade_id %s'%(t.tid)
        if t.tid:
            psi_queryset = PackageSkuItem.objects.filter(sale_trade_id=t.tid)
            #print 'psi_queryset count %d'%(psi_queryset.count())
            if psi_queryset.count() == 0:
                continue
            temp_sid = ''
            for psi in psi_queryset:
                #print 'get logistics %s %s'%(psi.out_sid, psi.logistics_company_code)
                if psi.out_sid and psi.logistics_company_code and temp_sid != psi.out_sid:
                    num = num+1
                    get_third_apidata_by_packetid.delay(psi.out_sid, psi.logistics_company_code)
                    temp_sid = psi.out_sid
    logger = logging.getLogger(__name__)
    logger.warn('update_all_logistics trades counts=%d, update counts=%d' % (sale_trades.count(), num))

@task()
def update_all_return_logistics():     #by huazi
    from flashsale.restpro.v1.views_wuliu_new import get_third_apidata_by_packetid_return
    salerefunds = SaleRefund.objects.filter(status__in=[SaleRefund.REFUND_WAIT_RETURN_GOODS,
                                                        SaleRefund.REFUND_CONFIRM_GOODS])
    from shopback.logistics.models import LogisticsCompany
    # logger.warn(len(salerefunds))
    for i in salerefunds:
        # logger.warn('遍历salerefunds')
        if i.company_name:
            company_id = LogisticsCompany.objects.filter(name=i.company_name).first()
            if not company_id:
                lc = LogisticsCompany.objects.values("name")
                head = i.company_name.encode('gb2312').decode('gb2312')[0:2].encode('utf-8')
                sim = [j['name'] for j in lc if j['name'].find(head)!=-1]
                if len(sim):
                    company_id = LogisticsCompany.objects.get(name=sim[0])
            if company_id and i.sid:
                # logging.warn("物流公司代码和物流单号都存在")
                get_third_apidata_by_packetid_return(i.id,i.sid,company_id.express_key)
                logging.warn("物流公司express_key%s,物流单号%s" % (company_id.express_key,i.sid))
    logger.warn('update_all_return_logistics')

@task()
def update_all_return_logistics_bykdn():
    from flashsale.restpro.v1.views_wuliu_new import get_third_apidata_by_packetid_return
    salerefunds = SaleRefund.objects.filter(status__in=[SaleRefund.REFUND_WAIT_RETURN_GOODS,
                                                        SaleRefund.REFUND_CONFIRM_GOODS])
    from shopback.logistics.models import LogisticsCompany
    # logger.warn(len(salerefunds))
    for i in salerefunds:
        # logger.warn('遍历salerefunds')
        if i.company_name:
            company_id = LogisticsCompany.objects.filter(name=i.company_name).first()
            if not company_id:
                lc = LogisticsCompany.objects.values("name")
                head = i.company_name.encode('gb2312').decode('gb2312')[0:2].encode('utf-8')
                sim = [j['name'] for j in lc if j['name'].find(head)!=-1]
                if len(sim):
                    company_id = LogisticsCompany.objects.get(name=sim[0])
            if company_id and i.sid:
                # logging.warn("物流公司代码和物流单号都存在")
                kdn_sub(i.id,i.company_name,i.sid)
                logging.warn("物流公司%s,物流单号%s" % (i.company_name,i.sid))
    logger.warn('update_all_return_logistics')

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
