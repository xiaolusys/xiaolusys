# -*- coding:utf-8 -*-
from django.db.models import Sum
from .models import OrderList, OrderDetail


def getProductOnTheWayNum(pId, skuId=None, start_time=None):
    """ 获取特卖商品在途数 """

    order_details = OrderDetail.objects.filter(product_id=pId) \
        .exclude(orderlist__status__in=(OrderList.SUBMITTING, OrderList.ZUOFEI))
    if skuId:
        order_details = order_details.filter(chichu_id=skuId)
    if start_time:
        order_details = order_details.filter(created__gt=start_time)
    details_dict = order_details.aggregate(total_buy_quantity=Sum('buy_quantity'),
                                           total_arrival_quantity=Sum('arrival_quantity'),
                                           total_inferior_quantity=Sum('inferior_quantity'))

    if details_dict['total_buy_quantity'] is None:
        return 0
    wait_receive_num = (details_dict['total_buy_quantity']
                        - details_dict['total_arrival_quantity']
                        - details_dict['total_inferior_quantity'])

    return max(wait_receive_num, 0)
