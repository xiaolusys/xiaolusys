import logging
import json
import sys
from django.db import IntegrityError, transaction
from django.db.models import Sum
from celery.task import task

from shopback.items.models import ProductSkuStats, ProductSku
logger = logging.getLogger(__name__)


def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    # return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


@task()
def task_productsku_create_productskustats(sku_id, product_id):
    from shopback.items.models import ProductSkuStats
    stats = ProductSkuStats.objects.filter(sku_id=sku_id)
    if stats.count() <= 0:
        stat = ProductSkuStats(sku_id=sku_id,product_id=product_id)
        stat.save()


@task()
@transaction.atomic
def task_productsku_update_productskustats(sku_id, product_id):
    stats = ProductSkuStats.objects.filter(sku_id=sku_id)
    if stats.count() <= 0:
        stat = ProductSkuStats(sku_id=sku_id, product_id=product_id)
        stat.save()


@task(max_retries=3, default_retry_delay=6)
def task_product_upshelf_update_productskusalestats(sku_id):
    """
    Recalculate and update init_waitassign_num,sale_start_time.
    """
    from shopback.items.models import ProductSku, ProductSkuStats, \
        ProductSkuSaleStats, gen_productsksalestats_unikey

    product = ProductSku.objects.get(id=sku_id).product
    product_id = product.id
    sku_stats = ProductSkuStats.get_by_sku(sku_id)
    wait_assign_num = sku_stats.wait_assign_num

    stats_uni_key = gen_productsksalestats_unikey(sku_id)
    stats = ProductSkuSaleStats.objects.filter(uni_key= stats_uni_key, sku_id=sku_id)

    if stats.count() == 0:
        try:
            stat = ProductSkuSaleStats(uni_key=stats_uni_key,
                                   sku_id=sku_id,
                                   product_id=product_id,
                                   init_waitassign_num=wait_assign_num,
                                   sale_start_time=product.sale_time)
            stat.save()
        except IntegrityError as exc:
            logger.warn("IntegrityError - productskusalestat/init_waitassign_num | sku_id: %s, init_waitassign_num: %s" % (
                sku_id, wait_assign_num))
            raise task_product_upshelf_update_productskusalestats.retry(exc=exc)
    else:
        logger.warn("RepeatUpshelf- productskusalestat/init_waitassign_num | sku_id: %s, init_waitassign_num: %s" % (
        sku_id, wait_assign_num))


@task(max_retries=3, default_retry_delay=6)
def task_product_downshelf_update_productskusalestats(sku_id, sale_end_time):
    """
    Recalculate and update sale_end_time,status.
    """
    from shopback.items.models import ProductSku, ProductSkuStats, \
        ProductSkuSaleStats, gen_productsksalestats_unikey

    product = ProductSku.objects.get(id=sku_id).product
    product_id = product.id

    stats_uni_key   = gen_productsksalestats_unikey(sku_id)
    stats = ProductSkuSaleStats.objects.filter(uni_key= stats_uni_key, sku_id=sku_id)

    if stats.count() > 0:
        try:
            stat = stats[0]
            stat.sale_end_time = sale_end_time
            stat.status = ProductSkuSaleStats.ST_FINISH
            stat.save(update_fields=["sale_end_time","status"])
        except IntegrityError as exc:
            logger.warn("IntegrityError - productskusalestat/init_waitassign_num | sku_id: %s, sale_end_time: %s" % (
                sku_id, sale_end_time))
            raise task_product_downshelf_update_productskusalestats.retry(exc=exc)

    else:
        logger.warn("RepeatDownshelf- productskusalestat/init_waitassign_num | sku_id: %s, sale_end_time: %s" % (
            sku_id, sale_end_time))


@task()
def task_product_upshelf_notify_favorited_customer(modelproduct):
    from flashsale.push.app_push import AppPush
    customer_ids = modelproduct.favorites_set.values('customer_id')

    for customer_id in customer_ids:
        AppPush.push_product_to_customer(customer_id['customer_id'], modelproduct)


@task()
def task_packageskuitem_update_productskustats(sku_id):
    """
    1) we added db_index=True for pay_time in packageskuitem;
    2) we should built joint-index for (sku_id, assign_status,pay_time)?
    -- Zifei 2016-04-18
    """
    from shopback.trades.models import PackageSkuItem
    logger.info("%s -sku_id:%s" % (get_cur_info(), sku_id))
    sum_res = PackageSkuItem.objects.filter(sku_id=sku_id, pay_time__gt=ProductSkuStats.PRODUCT_SKU_STATS_COMMIT_TIME). \
        exclude(assign_status=PackageSkuItem.CANCELED).values("assign_status").annotate(total=Sum('num'))
    wait_assign_num, assign_num, post_num, third_assign_num= 0, 0, 0, 0

    for entry in sum_res:
        if entry["assign_status"] == PackageSkuItem.NOT_ASSIGNED:
            wait_assign_num = entry["total"]
        elif entry["assign_status"] == PackageSkuItem.ASSIGNED:
            assign_num = entry["total"]
        elif entry["assign_status"] == PackageSkuItem.FINISHED:
            post_num = entry["total"]
        elif entry['assign_status'] == PackageSkuItem.VIRTUAL_ASSIGNED:
            third_assign_num = entry["total"]
    sold_num = wait_assign_num + assign_num + post_num + third_assign_num
    params = {"sold_num": sold_num, "assign_num": assign_num, "post_num": post_num}
    klogger = logging.getLogger('service')
    klogger.info({
        'action': 'skustat.pstat.task_packageskuitem_update_productskustats',
        'sku_id': sku_id,
        'params': json.dumps(params),
    })
    stat = ProductSkuStats.get_by_sku(sku_id)
    update_fields = []
    for k, v in params.iteritems():
        if hasattr(stat, k):
            if getattr(stat, k) != v:
                setattr(stat, k, v)
                update_fields.append(k)
    if update_fields:
        update_fields.append('modified')
        stat.save(update_fields=update_fields)


@task
def task_refundproduct_update_productskustats_return_quantity(sku_id):
    from shopback.refunds.models import RefundProduct
    logger.info("%s -sku_id:%s" % (get_cur_info(), sku_id))
    sum_res = RefundProduct.objects.filter(sku_id=sku_id, created__gt=ProductSkuStats.PRODUCT_SKU_STATS_COMMIT_TIME, can_reuse=True)\
        .aggregate(total=Sum('num'))
    total = sum_res["total"] or 0
    stat = ProductSkuStats.get_by_sku(sku_id)
    if stat.return_quantity != total:
        stat.return_quantity = total
        stat.save(update_fields=['return_quantity'])


@task(max_retries=3, default_retry_delay=6)
def task_orderdetail_update_productskustats_inbound_quantity(sku_id):
    """
    Whenever we have products inbound, we update the inbound quantity.
    0) OrderDetail arrival_time add db_index=True
    1) we should build joint-index for (sku,arrival_time)?
    --Zifei 2016-04-18
    """
    from flashsale.dinghuo.models import OrderDetail
    logger.info("%s -sku_id:%s" % (get_cur_info(), sku_id))
    sum_res = OrderDetail.objects.filter(chichu_id=sku_id,
                                         arrival_time__gt=ProductSkuStats.PRODUCT_SKU_STATS_COMMIT_TIME) \
        .aggregate(total=Sum('arrival_quantity'))
    total = sum_res["total"] or 0
    stat = ProductSkuStats.get_by_sku(sku_id)
    if stat.inbound_quantity != total:
        stat.inbound_quantity = total
        stat.save(update_fields=['inbound_quantity', 'modified'])


@task()
def task_update_product_sku_stat_rg_quantity(sku_id):
    from flashsale.dinghuo.models.purchase_return import RGDetail, ReturnGoods
    logger.info("%s -sku_id:%s" % (get_cur_info(), sku_id))
    sum_res = RGDetail.objects.filter(skuid=sku_id,
                                      created__gte=ProductSkuStats.PRODUCT_SKU_STATS_COMMIT_TIME,
                                      return_goods__status__in=[ReturnGoods.DELIVER_RG,
                                                                ReturnGoods.REFUND_RG,
                                                                ReturnGoods.SUCCEED_RG],
                                      type=RGDetail.TYPE_REFUND).aggregate(total=Sum('num'))
    total = sum_res["total"] or 0
    stat = ProductSkuStats.get_by_sku(sku_id)
    if stat.rg_quantity != total:
        stat.rg_quantity = total
        stat.save(update_fields=['rg_quantity'])


@task(max_retries=3, default_retry_delay=6)
def task_shoppingcart_update_productskustats_shoppingcart_num(sku_id):
    """
    Recalculate and update shoppingcart_num.
    """
    from flashsale.pay.models import ShoppingCart
    try:
        product_id = ProductSku.objects.get(id=sku_id).product.id
        shoppingcart_num_res = ShoppingCart.objects.filter(item_id=product_id,sku_id=sku_id,status=ShoppingCart.NORMAL).aggregate(
            Sum('num'))
        total = shoppingcart_num_res['num__sum'] or 0
        stat = ProductSkuStats.get_by_sku(sku_id)
        if stat.shoppingcart_num != total:
            stat.shoppingcart_num = total
            stat.save(update_fields=["shoppingcart_num"])
    except IntegrityError as exc:
        logger.warn("IntegrityError - productskustat/shoppingcart_num | sku_id: %s, shoppingcart_num: %s" % (sku_id, total))
        raise task_shoppingcart_update_productskustats_shoppingcart_num.retry(exc=exc)


@task(max_retries=3, default_retry_delay=6)
def task_saleorder_update_productskustats_waitingpay_num(sku_id):
    """
    Recalculate and update post_num.
    """
    from flashsale.pay.models import SaleOrder

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
