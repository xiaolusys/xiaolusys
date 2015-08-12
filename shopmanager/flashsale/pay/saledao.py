#-*- encoding:utf8 -*-
import datetime
from .models import SaleOrder,ShoppingCart
 
def getUserSkuNumByLast24Hours(user,sku):
    """ 获取用户过去24小时拍下商品规格数量 """
    last_24hour = datetime.datetime.now() - datetime.timedelta(days=1)
    sorders = SaleOrder.objects.filter(
                sale_trade__buyer_id=user.id,
                sku_id=sku.id,
                status__in=(SaleOrder.WAIT_BUYER_PAY,
                            SaleOrder.WAIT_SELLER_SEND_GOODS,
                            SaleOrder.WAIT_BUYER_CONFIRM_GOODS),
                pay_time__gte=last_24hour)
     
    shop_carts = ShoppingCart.objects.filter(
                    buyer_id=user.id,sku_id=sku.id,
                    status=ShoppingCart.NORMAL)
    order_num = 0
    for order in sorders:
        order_num += order.num
         
    for cart in shop_carts:
        order_num += cart.num
     
    return order_num