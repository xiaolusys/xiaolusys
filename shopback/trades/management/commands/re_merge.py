# coding=utf-8

from django.core.management.base import BaseCommand
import json
from shopback.trades.models import PackageSkuItem,PackageOrder
from shopback.logistics.models import LogisticsCompany

## 重新合单
##起因是有一些单子第三方发货改成仓库发货的时候, 有一些单子合进了第三方的包裹中,

##用法 python manage.py re_merge -id 202753 -wb 1
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-id', '--package_sku_item_id', action='store', dest='package_sku_item_id',
            type=str,
        )

        parser.add_argument(
            '-wb', '--ware_by', action='store', dest='ware_by',
            type=str,
        )
    def handle(self, *args, **options):
        id = options.get("package_sku_item_id")
        ware_by = options.get("ware_by")
        PackageSkuItem.objects.filter(id=id).update(ware_by=ware_by,package_order_pid=None)
        psi = PackageSkuItem.objects.get(id=id)
        psi.merge()