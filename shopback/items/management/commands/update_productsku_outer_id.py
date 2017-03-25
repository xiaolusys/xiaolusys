# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

import datetime
from django.db.models import Q
from shopback.items.models import Product, ProductSku
from flashsale.pay.models import ModelProduct
from flashsale.pay.models import SaleOrder, SaleRefund
from shopback.refunds.models import Refund, RefundProduct

from shopback.trades.models import PackageSkuItem
from flashsale.dinghuo.models import SupplyChainStatsOrder


class Command(BaseCommand):
    """ 更新productsku outer_id """
    def handle(self, *args, **kwargs):

        # model_ids = list(ModelProduct.objects.filter(
        #     Q(shelf_status=ModelProduct.ON_SHELF)|Q(modified__gte=datetime.datetime(2017,1,1))
        # ).values_list('id', flat=True))
        #
        # product_ids = list(Product.objects.filter(model_id__in=model_ids).values_list('id', flat=True))
        codes = open('/home/meron/Desktop/dumpdata/2017-03-25/SKU2017-03-25.csv','r').readlines()
        codes = [s.strip() for s in codes]
        product_skus  = ProductSku.objects.filter(outer_id__in=codes)
        # sku_product_code_maps = dict(product_skus.values_list('id', 'product__outer_id'))

        print 'total productskus:', product_skus.count()
        cnt = 1
        for sku in product_skus.only('id', 'outer_id', 'barcode').iterator():

            product_code = sku.product.outer_id
            origin_skucode = sku.outer_id
            # if not sku.outer_id.startswith(product_code):
            #     sku.outer_id = product_code + sku.outer_id
            sku.outer_id = sku.outer_id.replace(' ','') + str(cnt)
            if not sku.barcode:
                sku.barcode = sku.outer_id

            sku.save(update_fields=['outer_id', 'barcode'])

            if not sku.outer_id == origin_skucode:
                sorow   = SaleOrder.objects.filter(sku_id=sku.id).update(outer_sku_id=sku.outer_id)
                packrow = PackageSkuItem.objects.filter(sku_id=sku.id).update(outer_sku_id=sku.outer_id)
                suprow  = SupplyChainStatsOrder.objects.filter(product_id=product_code, outer_sku_id=origin_skucode) \
                    .update(outer_sku_id=sku.outer_id)
                RefundProduct.objects.filter(sku_id=sku.id).update(outer_sku_id=sku.outer_id)

            cnt += 1
            if cnt % 1000 == 0: print 'count=', cnt






