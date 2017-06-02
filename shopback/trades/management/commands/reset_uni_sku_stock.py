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
        ss = SkuStock.objects.filter(product__category=1)
        for i in ss:
            if i.realtime_quantity != 0:
                i.history_quantity = i.history_quantity - i.realtime_quantity
                i.save()


