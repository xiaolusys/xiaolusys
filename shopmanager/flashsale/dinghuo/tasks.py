# -*- coding:utf-8 -*-
__author__ = 'yann'
from celery.task import task
from shopback.items.models import Product, ProductSku
from flashsale.dinghuo.models_stats import SupplyChainDataStats
from flashsale.dinghuo.models import OrderDetail, OrderList
import functions
import datetime
import function_of_task
import urllib2
import re


@task(max_retry=3, default_retry_delay=5)
def task_stats_daily_order_by_group(pre_day=1):
    try:
        today = datetime.date.today()
        target_day = today - datetime.timedelta(days=pre_day)
        start_dt = datetime.datetime(target_day.year, target_day.month, target_day.day)
        end_dt = datetime.datetime(target_day.year, target_day.month, target_day.day, 23, 59, 59)
        order_qs = functions.get_source_orders(start_dt, end_dt)

        order_dict = functions.get_product_from_order(order_qs)
        data_stats_dict = {
            u"采购A": {"total_sale_num": 0, "total_cost_amount": 0, "total_sale_amount": 0,
                     "total_order_goods_quantity": 0, "total_order_goods_amount": 0},
            u"采购B": {"total_sale_num": 0, "total_cost_amount": 0, "total_sale_amount": 0,
                     "total_order_goods_quantity": 0, "total_order_goods_amount": 0},
            u"采购C": {"total_sale_num": 0, "total_cost_amount": 0, "total_sale_amount": 0,
                     "total_order_goods_quantity": 0, "total_order_goods_amount": 0}}
        for pro_id, sale_detail in order_dict.items():
            pro_bean = Product.objects.get(outer_id=pro_id)
            group = pro_bean.sale_group
            if group != u"None":
                group_name = group.name
                total_sale_num, total_cost_amount, total_sale_amount = 0, 0, 0
                for sku_outer_id, order_bean in sale_detail.items():
                    sku_qs = ProductSku.objects.filter(product__outer_id=pro_id, outer_id=sku_outer_id)
                    cost, agent_price = 0, 0
                    if sku_qs.count() > 0:
                        cost = sku_qs[0].cost
                        agent_price = sku_qs[0].agent_price
                        total_sale_num += order_bean['num']
                        total_cost_amount += order_bean['num'] * cost
                        total_sale_amount += order_bean['num'] * agent_price

                if group_name in data_stats_dict:
                    data_stats_dict[group_name]['total_sale_num'] += total_sale_num
                    data_stats_dict[group_name]['total_cost_amount'] += total_cost_amount
                    data_stats_dict[group_name]['total_sale_amount'] += total_sale_amount

        dinghuo_qs = OrderDetail.objects.exclude(orderlist__status=u'作废').filter(created__gte=start_dt,
                                                                                 created__lte=end_dt)
        for product_of_ding in dinghuo_qs:
            pro_bean = Product.objects.filter(id=product_of_ding.product_id)

            if pro_bean.count() > 0 and pro_bean[0].sale_group != u"None" and (
                pro_bean[0].sale_group.name in data_stats_dict):
                data_stats_dict[pro_bean[0].sale_group.name][
                    'total_order_goods_quantity'] += product_of_ding.buy_quantity
                data_stats_dict[pro_bean[0].sale_group.name]['total_order_goods_amount'] += product_of_ding.total_price

        for group_name, data_of_group in data_stats_dict.items():
            temp_data_stats = SupplyChainDataStats.objects.filter(stats_time=target_day, group=group_name)
            if temp_data_stats.count() > 0:
                data_stats_bean = temp_data_stats[0]
                data_stats_bean.sale_quantity = data_of_group['total_sale_num']
                data_stats_bean.cost_amount = data_of_group['total_cost_amount']
                data_stats_bean.turnover = data_of_group['total_sale_amount']
                data_stats_bean.order_goods_quantity = data_of_group['total_order_goods_quantity']
                data_stats_bean.order_goods_amount = data_of_group['total_order_goods_amount']
                data_stats_bean.save()
            else:
                new_order = SupplyChainDataStats(stats_time=target_day, group=group_name)
                new_order.sale_quantity = data_of_group['total_sale_num']
                new_order.cost_amount = data_of_group['total_cost_amount']
                new_order.turnover = data_of_group['total_sale_amount']
                new_order.order_goods_quantity = data_of_group['total_order_goods_quantity']
                new_order.order_goods_amount = data_of_group['total_order_goods_amount']
                new_order.save()
    except Exception, exc:
        raise task_stats_daily_order_by_group.retry(exc=exc)


@task(max_retry=3, default_retry_delay=5)
def task_stats_daily_product(pre_day=1):
    try:
        function_of_task.get_daily_order_stats(pre_day)
        function_of_task.get_daily_ding_huo_stats(pre_day)
        function_of_task.get_daily_goods_arrival_stats(pre_day)
        function_of_task.get_daily_out_order_stats(pre_day)
    except Exception, exc:
        raise task_stats_daily_order_by_group.retry(exc=exc)


@task(max_retry=3, default_retry_delay=5)
def task_stats_product():
    try:
        function_of_task.daily_data_stats()

    except Exception, exc:
        raise task_stats_daily_order_by_group.retry(exc=exc)


@task(max_retry=3, default_retry_delay=5)
def task_send_daily_message():
    try:
        corp_id = "wx1657da9bb74c42d3"
        corp_secret = "UuTTtiSINnX5X2fVEbGNXO82wHRa8mae5nhAJ1K4foLMwtGUXSRYRtgyDWPegJci"
        access_token = functions.get_token_in_time(corp_id, corp_secret)
        result_str = functions.get_result_daily()
        functions.send_txt_msg(access_token, result_str)
    except Exception, exc:
        raise task_send_daily_message.retry(exc=exc)


@task(max_retry=3, default_retry_delay=5)
def task_write_supply_name():
    try:
        all_data = OrderList.objects.exclude(status=u'作废').exclude(status=u'7')
        for data in all_data:
            if len(data.supplier_name) > 0:
                data.supplier_shop = get_supply_name(data.supplier_name)
                data.save()
    except Exception, exc:
        raise task_write_supply_name.retry(exc=exc)


def get_supply_name(name):
    if len(name) > 0:
        url_str = str(name)
    else:
        return ""
    try:
        content = urllib2.urlopen(url_str).read()
        reg = r'<a href=".*">首页</a>'
        content = str(content.decode('gb2312', 'ignore'))
        re_ = re.compile(reg)
        result = re.findall(re_, content)
        if result:
            return result[0].split("//")[1].split(".")[0]
        else:
            reg = r'<a data-spm="d21" href=".*" target="_blank">进入店铺</a>'
            re_ = re.compile(reg)
            result = re.findall(re_, content)
            if result:
                return result[0].split("//")[1].split(".")[0]
            else:
                return ""
    except Exception, ex:
        return ""