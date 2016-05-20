# coding=utf-8
__author__ = 'jishu_linjie'
from django.core.management.base import BaseCommand


from django.conf import settings

from shopback.trades.models import PackageSkuItem, PackageOrder
from flashsale.pay.models import SaleOrder


class Command(BaseCommand):
    def handle(self, *args, **options):
        items = PackageSkuItem.objects.filter(assign_status=2)
        for item in items:
            id = item.sale_order_id
            sale_order = SaleOrder.objects.filter(id=id).first()
            params = {}
            if sale_order:
                if not item.oid:
                    params.update({'oid':sale_order.oid})
                params.update({'receiver_mobile':sale_order.sale_trade.receiver_mobile, 'sale_trade_id':sale_order.sale_trade.tid})
            package_order = PackageOrder.objects.filter(pid=item.package_order_pid).first()
            if package_order and package_order.out_sid:
                params.update({'out_sid':package_order.out_sid, 'logistics_company_name':package_order.logistics_company.name, 'logistics_company_code':package_order.logistics_company.code})

            PackageSkuItem.objects.filter(id=item.id).update(**params)

