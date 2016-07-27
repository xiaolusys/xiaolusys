# coding=utf-8
from .models import (
    SaleSupplier,
    SaleCategory,
    SaleProduct,
    SaleProductManage,
    SaleProductManageDetail,
    SupplierFigure
)
from rest_framework import serializers


class SupplierStatusField(serializers.Field):
    def to_representation(self, obj):
        for record in SaleSupplier.STATUS_CHOICES:
            if record[0] == obj:
                return record[1]
        return ""

    def to_internal_value(self, data):
        return data


class ProgressField(serializers.Field):
    def to_representation(self, obj):
        for record in SaleSupplier.PROGRESS_CHOICES:
            if record[0] == obj:
                return record[1]
        return ""

    def to_internal_value(self, data):
        return data


class SaleCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleCategory
        fields = ('id', 'name', 'full_name', 'created', 'modified')


class SupplierFigureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierFigure
        fields = (
            'schedule_num',
            'no_pay_num',
            'pay_num',
            'cancel_num',
            'out_stock_num',
            'return_good_num',
            'return_good_rate',
            'payment',
            'cancel_amount',
            'out_stock_amount',
            'return_good_amount',
            'avg_post_days',
        )


class SaleSupplierSerializer(serializers.ModelSerializer):
    # category = SaleCategorySerializer()
    status = SupplierStatusField()
    progress = ProgressField()
    refund_rate = serializers.SerializerMethodField("calculate_refund_rate", read_only=True)
    figures = SupplierFigureSerializer(read_only=True)

    class Meta:
        model = SaleSupplier
        fields = ('id', 'supplier_name', 'supplier_code', 'brand_url', 'total_sale_num', 'refund_rate',
                  'progress', 'category', 'status', 'created', 'modified', 'memo', 'figures')

    def calculate_refund_rate(self, obj):
        """ 计算供应商的退货率 """
        return "%0.2f" % (obj.total_refund_num / obj.total_sale_num) if obj.total_sale_num > 0 else "0.0"


class PlatformField(serializers.Field):
    def to_representation(self, obj):
        for record in SaleProduct.PLATFORM_CHOICE:
            if record[0] == obj:
                return record[1]
        return ""

    def to_internal_value(self, data):
        return data


class StatusField(serializers.Field):
    def to_representation(self, obj):
        for record in SaleProduct.STATUS_CHOICES:
            if record[0] == obj:
                return record[1]
        return ""

    def to_internal_value(self, data):
        return data


class SaleProductSerializer(serializers.ModelSerializer):
    sale_supplier = SaleSupplierSerializer(read_only=True)
    sale_category = SaleCategorySerializer()
    status = StatusField()
    platform = PlatformField()
    sale_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = SaleProduct
        fields = (
            'id', 'outer_id', 'title', 'price', 'pic_url', 'product_link', 'sale_supplier', 'contactor',
            'sale_category','platform', 'hot_value', 'sale_price', 'on_sale_price', 'std_sale_price',
            'memo', 'status', 'sale_time', 'created', 'modified', 'reserve_time', 'supplier_sku', 'remain_num',
            'orderlist_show_memo')


class SaleProductUpdateSerializer(serializers.ModelSerializer):
    status = StatusField()
    platform = PlatformField()
    sale_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    orderlist_show_memo = serializers.NullBooleanField()

    class Meta:
        model = SaleProduct
        fields = (
            'id', 'outer_id', 'title', 'price', 'pic_url', 'product_link', 'sale_supplier', 'contactor',
            'sale_category','platform', 'hot_value', 'sale_price', 'on_sale_price', 'std_sale_price',
            'memo', 'status', 'sale_time', 'created', 'modified', 'reserve_time', 'supplier_sku', 'remain_num',
            'orderlist_show_memo')

from statistics.serializers import ModelStatsSimpleSerializer


class SimpleSaleProductSerializer(serializers.ModelSerializer):
    sale_supplier = SaleSupplierSerializer(read_only=True)
    sale_category = SaleCategorySerializer(read_only=True)
    status = StatusField()
    contactor = serializers.CharField(source='contactor.username', read_only=True)
    latest_figures = ModelStatsSimpleSerializer(source='sale_product_figures', read_only=True)

    class Meta:
        model = SaleProduct
        fields = (
            'id', 'outer_id', 'title', 'price', 'pic_url', 'product_link','status', 'sale_supplier', 'contactor',
            'sale_category', 'platform', 'hot_value', 'sale_price', 'on_sale_price', 'std_sale_price', 'memo',
            'sale_time', 'created', 'modified', 'supplier_sku', 'remain_num', 'latest_figures'
            )


class SimpleSaleProductManageSerializer(serializers.ModelSerializer):
    # category = SaleCategorySerializer()

    class Meta:
        model = SaleProductManage
        fields = ('id', 'schedule_type', 'sale_time', 'product_num', 'sale_supplier_num', "sale_suppliers",
                  'responsible_person_name', 'responsible_people_id', 'lock_status', 'created', 'modified',
                  'upshelf_time', 'offshelf_time')


class SaleProductManageSerializer(serializers.ModelSerializer):
    # category = SaleCategorySerializer()
    sale_suppliers = SaleSupplierSerializer(many=True)

    class Meta:
        model = SaleProductManage
        fields = ('id', 'schedule_type', 'sale_time', 'sale_suppliers', 'product_num', 'upshelf_time', 'offshelf_time',
                  'responsible_person_name', 'responsible_people_id', 'lock_status', 'created', 'modified')


class MaterialStatusField(serializers.Field):
    def to_representation(self, obj):
        for record in SaleProductManageDetail.MATERIAL_STATUS:
            if record[0] == obj:
                return record[1]
        return ""

    def to_internal_value(self, data):
        return data


class DesignTakeStatusField(serializers.Field):
    def to_representation(self, obj):
        for record in SaleProductManageDetail.DESIGN_TAKE_STATUS:
            if record[0] == obj:
                return record[1]
        return ""

    def to_internal_value(self, data):
        return data


class ManageDetailUseStatusField(serializers.Field):
    def to_representation(self, obj):
        for record in SaleProductManageDetail.USE_STATUS:
            if record[0] == obj:
                return record[1]
        return ""

    def to_internal_value(self, data):
        return data


class SaleProductManageDetailSerializer(serializers.ModelSerializer):

    # sale_category = SaleCategorySerializer()
    product_name = serializers.CharField(source='sale_product.title', read_only=True)
    product_purchase_price = serializers.CharField(source='sale_product.sale_price', read_only=True)
    product_sale_price = serializers.CharField(source='sale_product.on_sale_price', read_only=True)
    product_origin_price = serializers.CharField(source='sale_product.std_sale_price', read_only=True)
    product_pic = serializers.CharField(source='sale_product.pic_url', read_only=True)
    product_link = serializers.CharField(source='sale_product.product_link', read_only=True)
    model_id = serializers.IntegerField(source='product_model_id', read_only=True)
    material_status = MaterialStatusField()
    design_take_over = DesignTakeStatusField()
    today_use_status = ManageDetailUseStatusField()
    supplier_id = serializers.IntegerField(source='sale_product.sale_supplier.id', read_only=True)

    class Meta:
        model = SaleProductManageDetail
        fields = ('id', 'supplier_id', 'sale_product_id', 'product_name', 'product_pic', 'product_link', 'design_person', 'order_weight','model_id',
                  'sale_category', 'material_status', 'today_use_status', 'product_purchase_price', 'product_sale_price',
                  'product_origin_price', 'design_take_over', 'design_complete', 'is_approved', 'is_promotion',
                  'created', 'modified')


class SaleProductManageDetailSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = SaleProductManageDetail

