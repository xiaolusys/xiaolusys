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
            oid = item.sale_order_id
            sale_order = SaleOrder.objects.filter(oid=oid).first()
            update_fields = []
            if sale_order:
                item.receiver_mobile = sale_order.sale_trade.receiver_mobile
                update_fields.append('receiver_mobile')
                item.sale_trade_id = sale_order.sale_trade.tid
                update_fields.append('sale_trade_id')
            package_order = PackageOrder.objects.filter(pid=item.package_order_pid).first()
            if package_order and package_order.out_sid:
                item.out_sid = package_order.out_sid
                update_fields.append('out_sid')
                item.logistics_company_name = package_order.logistics_company.name
                update_fields.append('logistics_company_name')
                item.logistics_company_code = package_order.logistics_company.code
                update_fields.append('logistics_company_code')
            if update_fields:
                item.save(update_fields=update_fields)
        
