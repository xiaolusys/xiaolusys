# coding:utf-8
from rest_framework import serializers

from supplychain.supplier.models import SaleSupplier
from .models import LackGoodOrder
from .models.inbound import InBound

class SupplierSerializer(serializers.ModelSerializer):

    class Meta:
        model = SaleSupplier
        extra_kwargs = {}
        fields = (
        'id', 'supplier_name', 'supplier_code', 'status')


class LackGoodOrderSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(source='product.name', read_only=True)
    product_img = serializers.CharField(source='product.pic_path', read_only=True)
    sku_name  = serializers.CharField(source='product_sku.name', read_only=True)
    supplier = SupplierSerializer(read_only=True)

    class Meta:
        model = LackGoodOrder
        extra_kwargs = {}
        fields = (
        'id', 'supplier', 'product_id', 'sku_id', 'product_name', 'product_img', 'sku_name',
        'lack_num', 'refund_num', 'is_refund', 'refund_time', 'status')


class InBoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = InBound
        fields = ('id', 'status', 'ware_by')