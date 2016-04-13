# -*- coding:utf8 -*-

from django.db.models import Sum
from .models import Purchase, PurchaseItem
from shopback import paramconfig as pcfg


def getProductWaitReceiveNum(pId, skuId=None):
    purchaseItems = PurchaseItem.objects.filter(product_id=pId,
                                                purchase__status=pcfg.PURCHASE_APPROVAL, status=pcfg.NORMAL)

    if skuId:
        purchaseItems = purchaseItems.filter(sku_id=skuId)

    purchase_dict = purchaseItems.aggregate(total_purchase_num=Sum('purchase_num'),
                                            total_storage_num=Sum('storage_num'))
    if (purchase_dict['total_purchase_num'] is None or
                purchase_dict['total_storage_num'] is None):
        return 0
    return purchase_dict['total_purchase_num'] - purchase_dict['total_storage_num']
