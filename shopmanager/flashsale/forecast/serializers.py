from rest_framework import serializers

from supplychain.supplier.models import SaleSupplier
from .models import (
    ForecastInbound,
    ForecastInboundDetail,
    StagingInBound,
    RealInbound,
    RealInboundDetail,
    ForecastStats
)

from flashsale.dinghuo.models import OrderList, OrderDetail


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleSupplier
        extra_kwargs = {}
        fields = (
            'id', 'supplier_name', 'supplier_code', 'status')


class OrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetail
        extra_kwargs = {}
        fields = (
            'id', 'product_id', 'product_name', 'chichu_id', 'product_chicun', 'buy_quantity', 'created')


class OrderListSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)

    class Meta:
        model = OrderList
        extra_kwargs = {}
        fields = (
            'id', 'buyer_name', 'order_amount', 'supplier_name', 'supplier',
            'total_detail_num', 'created', 'status', 'status_name')


class ForecastInboundDetailSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_img = serializers.CharField(source='product_pic', read_only=True)
    sku_name = serializers.CharField(source='product_sku.name', read_only=True)

    class Meta:
        model = ForecastInboundDetail
        extra_kwargs = {}
        fields = (
            'id', 'product_id', 'sku_id', 'forecast_arrive_num', 'product_name', 'sku_name', 'product_img')


class SimpleForecastInboundSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)

    class Meta:
        model = ForecastInbound
        extra_kwargs = {}
        fields = (
            'id', 'supplier', 'express_code', 'express_no', 'forecast_arrive_time',
            'total_detail_num', 'real_arrive_num', 'purchaser', 'status', 'status_name',
            'memo', 'has_lack', 'has_defact', 'has_overhead', 'has_wrong')


class ForecastInboundSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)
    inbound_details = ForecastInboundDetailSerializer(source='details_manager', read_only=True, many=True)

    class Meta:
        model = ForecastInbound
        extra_kwargs = {}
        fields = (
            'id', 'supplier', 'inbound_details', 'express_code', 'express_no',
            'forecast_arrive_time', 'purchaser', 'status', 'status_name')


class StagingInBoundSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)
    forecast_inbound = ForecastInboundSerializer(read_only=True)

    class Meta:
        model = StagingInBound
        extra_kwargs = {}
        fields = (
        'id', 'wave_no', 'forecast_inbound', 'supplier', 'ware_house', 'product', 'record_num', 'creator', 'status')


class SimpleRealInboundSerializer(serializers.ModelSerializer):
    class Meta:
        model = RealInbound
        extra_kwargs = {}
        fields = ('id', 'wave_no', 'ware_house', 'express_code', 'express_no', 'creator', 'inspector',
                  'total_detail_num', 'total_inferior_num', 'created', 'memo', 'status', 'status_name')


class ForecastStatsSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.supplier_name', read_only=True)
    has_lack = serializers.IntegerField()
    has_defact = serializers.IntegerField()
    has_overhead = serializers.IntegerField()
    has_wrong = serializers.IntegerField()
    is_unrecordlogistic = serializers.IntegerField()
    is_timeout = serializers.IntegerField()
    is_lackclose = serializers.IntegerField()

    class Meta:
        model = ForecastStats
        extra_kwargs = {}
        fields = ('id', 'forecast_inbound', 'supplier_name', 'buyer_name', 'purchaser', 'purchase_num', 'inferior_num',
                  'lack_num', 'purchase_amount', 'purchase_time', 'delivery_time', 'arrival_time', 'billing_time',
                  'finished_time', 'has_lack', 'has_defact', 'has_overhead', 'has_wrong', 'is_unrecordlogistic',
                  'is_timeout', 'is_lackclose')


