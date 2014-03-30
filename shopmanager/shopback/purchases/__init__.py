#-*- coding:utf8 -*-

from django.db.models import Sum
from .models import Purchase,PurchaseItem
from shopback import paramconfig as pcfg

def getProductWaitReceiveNum(pId,skuId=None):
    
    purchaseItems = PurchaseItem.objects.filter(product_id=pId,
                                purchase__status=pcfg.PURCHASE_APPROVAL,status=pcfg.NORMAL)
                                
    if skuId:
        purchaseItems = purchaseItems.filter(sku_id=skuId)
                                
    wait_receive_num = purchaseItems.extra(select={'remain_num': "purchase_num-storage_num"})\
        .aggregate(total_remain_num=Sum('remain_num')).get('total_remain_num')
        
    return wait_receive_num