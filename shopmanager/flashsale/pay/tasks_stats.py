
from django.db import IntegrityError
from django.db.models import Sum
from celery.task import task

from flashsale.pay.models import ShoppingCart, SaleOrder

import logging
logger = logging.getLogger(__name__)

@task(max_retries=3, default_retry_delay=6)
def task_shoppingcart_update_productskustats_shoppingcart_num(sku_id):
    """
    Recalculate and update shoppingcart_num.
    """
    from  shopback.items.models import ProductSku, ProductSkuStats

    product_id = ProductSku.objects.get(id=sku_id).product.id
    shoppingcart_num_res = ShoppingCart.objects.filter(item_id=product_id,sku_id=sku_id,status=ShoppingCart.NORMAL).aggregate(
        Sum('num'))
    total = shoppingcart_num_res['num__sum'] or 0

    stats = ProductSkuStats.objects.filter(sku_id=sku_id)
    if stats.count() <= 0:
        try:
            stat = ProductSkuStats(sku_id=sku_id, product_id=product_id, shoppingcart_num=total)
            stat.save()
        except IntegrityError as exc:
            logger.warn("IntegrityError - productskustat/shoppingcart_num | sku_id: %s, shoppingcart_num: %s" % (sku_id, total))
            raise task_shoppingcart_update_productskustats_shoppingcart_num.retry(exc=exc)
    else:
        stat = stats[0]
        if stat.shoppingcart_num != total:
            stat.shoppingcart_num = total
            stat.save(update_fields=["shoppingcart_num"])


@task(max_retries=3, default_retry_delay=6)
def task_saleorder_update_productskustats_waitingpay_num(sku_id):
    """
    Recalculate and update post_num.
    """
    from  shopback.items.models import ProductSku, ProductSkuStats

    product_id = ProductSku.objects.get(id=sku_id).product.id
    waitingpay_num_res = SaleOrder.objects.filter(item_id=product_id, sku_id=sku_id,
                                                       status=SaleOrder.WAIT_BUYER_PAY).aggregate(
        Sum('num'))
    total = waitingpay_num_res['num__sum'] or 0

    stats = ProductSkuStats.objects.filter(sku_id=sku_id)
    if stats.count() <= 0:
        try:
            stat = ProductSkuStats(sku_id=sku_id, product_id=product_id, waitingpay_num=total)
            stat.save()
        except IntegrityError as exc:
            logger.warn(
                "IntegrityError - productskustat/waitingpay_num | sku_id: %s, waitingpay_num: %s" % (sku_id, total))
            raise task_saleorder_update_productskustats_waitingpay_num.retry(exc=exc)
    else:
        stat = stats[0]
        if stat.waitingpay_num != total:
            stat.waitingpay_num = total
            stat.save(update_fields=["waitingpay_num"])



@task()
def task_update_saletrade_statust():
    from flashsale.pay.models import *
    from django.db.models import Q
    so = SaleOrder.objects.filter(Q(refund_status=SaleRefund.REFUND_SUCCESS)|Q(refund_status=SaleRefund.REFUND_CLOSED),sale_trade__status=2)
    from flashsale.pay.tasks import tasks_update_sale_trade_status
    for instance in so:
        if instance.status > SaleOrder.WAIT_BUYER_PAY:
            tasks_update_sale_trade_status.delay(instance.sale_trade_id)