# coding: utf-8
import chardet
import datetime
import re

from django.core.management.base import BaseCommand
from django.db import connection

from core.options import log_action, CHANGE
from flashsale.pay.models import SaleOrder
from shopback.items.models import Product, ProductSku
from shopback.refunds.models import RefundProduct
from shopback.trades.models import MergeOrder, PackageSkuItem
from supplychain.supplier.models import SaleProduct

ADMIN_ID = 1


class Command(BaseCommand):
    PATTERN = re.compile(r'^[\w\-_]*$')

    def process_abnormal(self, sku):
        old_outer_id = sku.outer_id
        if sku.barcode:
            new_outer_id = sku.barcode
        else:
            new_outer_id = '%s%d' % (sku.product.outer_id, sku.id)
        ProductSku.objects.filter(id=sku.id).update(outer_id=new_outer_id)
        log_action(ADMIN_ID, sku, CHANGE, '更新outer_id, %s->%s' % (old_outer_id, new_outer_id))

        for sale_order in SaleOrder.objects.filter(sku_id=str(sku.id)):
            SaleOrder.objects.filter(id=sale_order.id).update(outer_sku_id=new_outer_id)
            log_action(ADMIN_ID, sale_order, CHANGE, '更新outer_sku_id, %s->%s' % (old_outer_id, new_outer_id))

        for merge_order in MergeOrder.objects.filter(outer_id=sku.product.outer_id, outer_sku_id=old_outer_id):
            MergeOrder.objects.filter(id=merge_order.id).update(outer_sku_id=new_outer_id)
            log_action(ADMIN_ID, merge_order, CHANGE, '更新outer_sku_id, %s->%s' % (old_outer_id, new_outer_id))

        for package_sku_item in PackageSkuItem.objects.filter(sku_id=str(sku.id)):
            PackageSkuItem.objects.filter(id=package_sku_item.id).update(outer_sku_id=new_outer_id)
            log_action(ADMIN_ID, package_sku_item, CHANGE, '更新outer_sku_id, %s->%s' % (old_outer_id, new_outer_id))

        for refund_product in RefundProduct.objects.filter(outer_id=sku.product.outer_id, outer_sku_id=old_outer_id):
            RefundProduct.objects.filter(id=refund_product.id).update(outer_sku_id=new_outer_id)
            log_action(ADMIN_ID, refund_product, CHANGE, '更新outer_sku_id, %s->%s' % (old_outer_id, new_outer_id))

    def handle(self, *args, **kwargs):
        cursor = connection.cursor()
        i = 0
        cursor.execute(
            'select count(1) from shop_items_productsku where LENGTH(outer_id) != CHAR_LENGTH(outer_id) or outer_id regexp "#"')
        row = cursor.fetchone()
        n = row[0]

        for sku in ProductSku.objects.raw(
                'select * from shop_items_productsku where LENGTH(outer_id) != CHAR_LENGTH(outer_id) or outer_id regexp "#"'):
            i += 1
            print '%s/%s' % (i, n)
            self.process_abnormal(sku)
