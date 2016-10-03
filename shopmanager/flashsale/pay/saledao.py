# -*- encoding:utf8 -*-
import datetime
from .models import SaleOrder, ShoppingCart


def getUserSkuNumByLast24Hours(user, sku):
    """ 获取用户过去48小时拍下商品规格数量 """
    last_48hour = datetime.datetime.now() - datetime.timedelta(days=2)
    order_nums = SaleOrder.objects.filter(
        buyer_id=user.id,
        sku_id=sku.id,
        status__in=(SaleOrder.WAIT_BUYER_PAY,
                    SaleOrder.WAIT_SELLER_SEND_GOODS,
                    SaleOrder.WAIT_BUYER_CONFIRM_GOODS),
        pay_time__gte=last_48hour).values_list('num', flat=True)
    return sum(order_nums)


