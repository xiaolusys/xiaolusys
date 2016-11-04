# coding=utf-8

from shopback.items.models import SkuStock, ProductSku


def init_product_sku_stats():
    for p in ProductSku.objects.exclude(quantity=0,wait_post_num=0):
        p.save()


def repair_history_quantity():
    for stat in SkuStock.objects.all():
        p = ProductSku.objects.get(id=stat.sku_id)
        stat.history_quantity = p.quantity - p.wait_post_num
        stat.save()
