# coding=utf-8

from django.core.management.base import BaseCommand
from shopback.items.models import SkuStock
import json
from shopback.trades.models import PackageSkuItem,PackageOrder
from shopback.logistics.models import LogisticsCompany

## 清空优尼世界的库存

##用法 python manage.py reset_package_order -id 202753,32131,321321
class Command(BaseCommand):
    # def add_arguments(self, parser):
    #     parser.add_argument(
    #         '-id', '--package_sku_item_id', action='store', dest='package_sku_item_id',
    #         type=str,
    #     )

    def handle(self, *args, **options):
        # ss = SkuStock.objects.filter(product__category__in=[8,5,9,12,13,14,15,16,17,18,19,20,21,22,25,26,27,59,60,61,62,63,64,])
        ss = SkuStock.objects.filter(product_id__in=SkuStock.filter_by_supplier(28802))
        for i in ss:
            if i.realtime_quantity != 0:
                i.history_quantity = i.history_quantity - i.realtime_quantity
                i.save()
        # for i in ss:
        #     if i.realtime_quantity != 0:
        #         i.history_quantity = i.history_quantity - i.realtime_quantity
        #         i.save()


