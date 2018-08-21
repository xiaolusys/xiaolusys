# coding=utf-8

from shopback.trades.models import PackageSkuItem, PackageOrder


def packing_skus(type=None, delay=True):
    """
        打包
    :return:
    """
    if delay:
        PackageSkuItem.packing_skus_delay(type)
    else:
        PackageSkuItem.batch_merge(type)
