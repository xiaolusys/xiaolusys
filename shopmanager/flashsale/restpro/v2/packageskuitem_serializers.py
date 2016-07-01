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
    
    class Meta:
        model = PackageSkuItem
        fields = ('title', 'pic_path', 'num', 'payment', 'assign_status_display', 'ware_by_display', 'out_sid',
                  'logistics_company_name', 'logistics_company_code', 'process_time', 'pay_time', 'book_time',
                  'assign_time', 'finish_time', 'cancel_time', 'package_group_key', 'note')



        



