# -*- coding:utf8 -*-

from shopback.items.models import SkuStock
from shopback.items.tasks import task_update_inferiorsku_return_quantity
from shopback.items.models import ProductSku
from shopback.refunds.models import RefundProduct
import logging
logger = logging.getLogger(__name__)

def return_good_into_stock(refund_product_id, outer_id, outer_sku_id,return_num):
    sku_id = ProductSku.get_by_outer_id(outer_id,outer_sku_id).id
    refund_product = RefundProduct.objects.filter(id=refund_product_id).first()
    if sku_id:
        RefundProduct.objects.filter(id=refund_product_id).update(sku_id=sku_id)
        if not refund_product.in_stock:
            refund_product.add_into_stock(return_num)
            refund_product.in_stock = True
            refund_product.save()
        task_update_inferiorsku_return_quantity.delay(sku_id)
    else:
        logger.warn({'action': "return_good_into_stock", 'info': 'ProductSku_id is not exist'})