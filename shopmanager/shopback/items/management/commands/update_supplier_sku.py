# coding: utf-8
import chardet
from core.options import log_action, CHANGE
import re

from django.core.management.base import BaseCommand

from flashsale.pay.models import SaleOrder
from shopback.trades.models import MergeOrder
from shopback.items.models import Product, ProductSku
from supplychain.supplier.models import SaleProduct


ADMIN_ID = 1


class Command(BaseCommand):
    PATTERN = re.compile(r'^[\w\-_#]*$')

    def process_abnormal(self, sku):
        old_outer_id = sku.outer_id
        if sku.barcode:
            new_outer_id = sku.barcode
        else:
            new_outer_id = '%s%d' % (sku.product.outer_id, sku.id)
        ProductSku.objects.filter(id=sku.id).update(outer_id=new_outer_id)
        log_action(ADMIN_ID, sku, CHANGE, '更新outer_id, %s->%s' % (old_outer_id, new_outer_id))

        for sale_order in SaleOrder.objects.filter(item_id=str(sku.product.id), outer_sku_id=old_outer_id):
            SaleOrder.objects.filter(id=sale_order.id).update(outer_sku_id=new_outer_id)
            log_action(ADMIN_ID, sale_order, CHANGE, '更新outer_sku_id, %s->%s' % (old_outer_id, new_outer_id))

        for merge_order in MergeOrder.objects.filter(outer_id=sku.product.outer_id, outer_sku_id=old_outer_id):
            MergeOrder.objects.filter(id=merge_order.id).update(outer_sku_id=new_outer_id)
            log_action(ADMIN_ID, merge_order, CHANGE, '更新outer_sku_id, %s->%s' % (old_outer_id, new_outer_id))


    def handle(self, *args, **kwargs):
        for sku in ProductSku.objects.filter(status=ProductSku.NORMAL):
            m = self.PATTERN.match(sku.outer_id)
            if not m:
                self.process_abnormal(sku)
