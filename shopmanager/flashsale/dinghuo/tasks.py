# -*- coding:utf-8 -*-
__author__ = 'yann'
from celery.task import task
from shopback.items.models import Product, ProductSku
from flashsale.dinghuo.models_stats import SupplyChainDataStats
from flashsale.dinghuo.models import OrderDetail
import functions
import datetime


@task(max_retry=3, default_retry_delay=5)
def task_stats_daily_order_by_group(pre_day=1):
    try:
        today = datetime.date.today()
        target_day = today - datetime.timedelta(days=pre_day)
        start_dt = datetime.datetime(target_day.year, target_day.month, target_day.day)
        end_dt = datetime.datetime(target_day.year, target_day.month, target_day.day, 23, 59, 59)
        order_qs = functions.get_source_orders(start_dt, end_dt)

        order_dict = functions.get_product_from_order(order_qs)
        data_stats_dict = {}
        for pro_id, sale_detail in order_dict.items():
            pro_bean = Product.objects.get(outer_id=pro_id)
            group_name = pro_bean.sale_group.name
            total_sale_num, total_cost_amount, total_sale_amount = 0, 0, 0
            for sku_outer_id, order_bean in sale_detail.items():
                sku_qs = ProductSku.objects.filter(product__outer_id=pro_id, outer_id=sku_outer_id)
                cost, agent_price = 0, 0
                if sku_qs.count() > 0:
                    cost = sku_qs[0].cost
                    agent_price = sku_qs[0].agent_price
                total_sale_num += order_bean['num']
                total_cost_amount += total_sale_num * cost
                total_sale_amount += total_sale_num * agent_price

            if group_name in data_stats_dict:
                data_stats_dict[group_name]['total_sale_num'] += total_sale_num
                data_stats_dict[group_name]['total_cost_amount'] += total_cost_amount
                data_stats_dict[group_name]['total_sale_amount'] += total_sale_amount
            else:
                data_stats_dict[group_name] = {"total_sale_num": total_sale_num,
                                               "total_cost_amount": total_cost_amount,
                                               "total_sale_amount": total_sale_amount,
                                               "total_order_goods_quantity": 0,
                                               "total_order_goods_amount": 0}
        dinghuo_qs = OrderDetail.objects.exclude(orderlist__status=u'作废').filter(created__gte=start_dt,
                                                                                 created__lte=end_dt)
        for product_of_ding in dinghuo_qs:
            pro_bean = Product.objects.get(id=product_of_ding.product_id)
            if pro_bean and (pro_bean.sale_group.name in data_stats_dict):
                data_stats_dict[group_name]['total_order_goods_quantity'] += product_of_ding.buy_quantity
                data_stats_dict[group_name]['total_order_goods_amount'] += product_of_ding.total_price
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
