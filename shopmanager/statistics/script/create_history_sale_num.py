# coding=utf-8
from statistics.tasks import task_update_sale_order_stats_record


def create_total_sale_num_by_packet():
    from flashsale.pay.models import SaleOrder
    orders = SaleOrder.objects.filter(created__gte='2016-4-15 00:00:00', created__lte='2016-4-16 23:59:59')
    for order in orders:
        task_update_sale_order_stats_record(order)
