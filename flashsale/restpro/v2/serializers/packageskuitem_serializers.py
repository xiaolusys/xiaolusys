# coding=utf-8
from rest_framework import serializers

from shopback.trades.models import (
    PackageOrder,
    PackageSkuItem,
)


class PackageSkuItemSerializer(serializers.ModelSerializer):
    process_time = serializers.CharField(read_only=True)
    package_group_key = serializers.CharField(read_only=True)
    ware_by_display = serializers.CharField(read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_id = serializers.CharField(source="product.id", read_only=True)
    sku_name = serializers.CharField(source="product_sku.product.name", read_only=True)
    class Meta:
        model = PackageSkuItem
        fields = ('id', 'oid','product_id', 'product_name','outer_id','sku_id','outer_sku_id','sku_name','title', 'pic_path', 'num', 'payment', 'assign_status_display', 'ware_by_display', 'out_sid',
                  'logistics_company_name', 'logistics_company_code', 'process_time', 'pay_time', 'book_time',
                  'assign_time', 'finish_time', 'cancel_time', 'package_group_key', 'note', 'package_order_pid','init_assigned','get_status_display','get_assign_status_display')
        # fields = ("product_name", "process_time", 'ware_by_display','package_group_key')



        



