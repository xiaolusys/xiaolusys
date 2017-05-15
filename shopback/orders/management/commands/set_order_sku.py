# coding=utf-8

from django.core.management.base import BaseCommand
from shopback.dinghuo.models_purchase import *
from shopback.orders.models import Order
from shopback.items.models import ProductSku,SkuStock


##处理天猫商城的单子和系统的ProductSKu不匹配问题
##使用方法: python manage.py -oid 19652008584767860 -sku 298997
##如果执行成功 那么 order表的sku方法会显示出来
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-oid', '--order_oid', action='store', dest='order_oid',
            type=str,
        )

        parser.add_argument(
            '-sku', '--SkuStock', action='store', dest='SkuStock',
            type=str,
        )

    def handle(self, *args, **options):
        oid = options.get('order_oid')
        sku = options.get('SkuStock')
        order = Order.objects.get(oid=oid)
        ss = SkuStock.objects.get(sku_id=sku)
        order.outer_id = ss.sku.product.outer_id
        order.outer_sku_id = ss.sku.outer_id
        order.save()
        order = Order.objects.get(oid=oid)
        print order.sku