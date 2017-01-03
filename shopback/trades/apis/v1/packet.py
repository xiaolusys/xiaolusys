# coding=utf-8

from shopback.trades.models import PackageSkuItem, PackageOrder


def packing_skus():
    """
        打包
    :return:
    """
    PackageSkuItem.packing_skus_delay()
