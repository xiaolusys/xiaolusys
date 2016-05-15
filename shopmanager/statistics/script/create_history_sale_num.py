# coding=utf-8
from statistics.models import StatisticSaleNum
from shopback.trades.models import PackageSkuItem
from statistics.models import StatisticSaleNum


def create_total_sale_num_by_packet():
    packets = PackageSkuItem.objects.all()
    for packet in packets:
        StatisticSaleNum.objects.create_and_update_sale_stat(sku_id=packet.sku_id, pay_time=packet.pay_time)
