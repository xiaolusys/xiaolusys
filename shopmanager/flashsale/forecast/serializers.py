
from rest_framework import serializers

from supplychain.supplier.models import SaleSupplier
from .models import ForecastInbound, ForecastInboundDetail, StagingInBound, RealInBound, RealInBoundDetail

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
    sku_name  = serializers.CharField(source='product_sku.name', read_only=True)

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
        'total_detail_num', 'purchaser', 'status', 'status_name')

class ForecastInboundSerializer(serializers.ModelSerializer):

    supplier = SupplierSerializer(read_only=True)
    inbound_details = ForecastInboundDetailSerializer(source='details_manager', read_only=True , many=True)

    class Meta:
        model = ForecastInbound
        extra_kwargs = {}
        fields = (
        'id', 'supplier', 'inbound_details', 'express_code', 'express_no',
        'forecast_arrive_time', 'purchaser', 'status', 'status_name')


class ForecastInboundDetailSerializer(serializers.ModelSerializer):


    class Meta:
        model = ForecastInboundDetail
        extra_kwargs = {}
        fields = (
        'id', 'product_id', 'sku_id', 'forecast_arrive_num', 'product_name', 'product_img')


class StagingInBoundSerializer(serializers.ModelSerializer):

    supplier = SupplierSerializer(read_only=True)
    forecast_inbound = ForecastInboundSerializer(read_only=True)

    class Meta:
        model = StagingInBound
        extra_kwargs = {}
        fields = ('id', 'wave_no', 'forecast_inbound', 'supplier', 'ware_house', 'product', 'record_num', 'creator','status')


class SimpleRealInBoundSerializer(serializers.ModelSerializer):

    class Meta:
        model = RealInBound
        extra_kwargs = {}
        fields = ('id', 'wave_no', 'ware_house', 'express_code', 'express_no', 'creator', 'inspector',
                  'total_detail_num', 'created', 'memo', 'status', 'status_name')


