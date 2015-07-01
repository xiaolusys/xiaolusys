# coding:utf-8
__author__ = 'yann'
from shopback.trades.models import MergeOrder
from flashsale.dinghuo import paramconfig as pcfg
from flashsale.dinghuo.models import OrderDetail, ProductSkuDetail
from django.db.models import Sum


def get_lack_num_by_product(product, sku):
    sale_num = get_sale_num(product, sku)
    ding_num = get_ding_num(product, sku)
    already_reach = get_already_num(product, sku)
    exist_stock_num = get_sample_num(sku)
    print sale_num, ding_num, already_reach,exist_stock_num
    return sale_num - ding_num - already_reach - exist_stock_num


def get_sale_num(product, sku):
    """获取上架后商品的销售"""
    order_qs = MergeOrder.objects.filter(sys_status=pcfg.IN_EFFECT) \
        .exclude(merge_trade__type=pcfg.REISSUE_TYPE) \
        .exclude(merge_trade__type=pcfg.EXCHANGE_TYPE) \
        .exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE)
    order_qs = order_qs.filter(pay_time__gte=product.sale_time)
    order_qs = order_qs.filter(merge_trade__status__in=pcfg.ORDER_SUCCESS_STATUS) \
        .exclude(merge_trade__sys_status__in=(pcfg.INVALID_STATUS, pcfg.ON_THE_FLY_STATUS)) \
        .exclude(merge_trade__sys_status=pcfg.FINISHED_STATUS, merge_trade__is_express_print=False)
    order_qs = order_qs.filter(outer_id=product.outer_id, outer_sku_id=sku.outer_id).aggregate(
        total_sale_num=Sum('num')).get('total_sale_num') or 0
    return order_qs


def get_ding_num(product, sku):
    print OrderDetail.objects.filter(orderlist__status__in=(u'草稿', u'审核', u'7')).filter(
        created__gte=product.sale_time).filter(product_id=product.id, chichu_id=sku.id)[1].orderlist
    return OrderDetail.objects.filter(orderlist__status__in=(u'草稿', u'审核', u'7')).filter(
        created__gte=product.sale_time).filter(product_id=product.id, chichu_id=sku.id).aggregate(
        total_num=Sum('buy_quantity')).get('total_num') or 0


def get_already_num(product, sku):
    return OrderDetail.objects.filter(orderlist__status__in=(u'5', u'6', u'有问题', u'已处理', u'验货完成')).filter(
        created__gte=product.sale_time).filter(product_id=product.id, chichu_id=sku.id).aggregate(
        total_num=Sum('arrival_quantity')).get('total_num') or 0


def get_sample_num(sku):
    return ProductSkuDetail.objects.filter(product_sku=sku.id).aggregate(
        total_num=Sum('exist_stock_num')).get('total_num') or 0