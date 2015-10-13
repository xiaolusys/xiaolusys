from .models import SaleSupplier, SaleCategory, SaleProduct
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


class SaleSupplierSerializer(serializers.ModelSerializer):
    # category = SaleCategorySerializer()
    status = SupplierStatusField()
    progress = ProgressField()

    class Meta:
        model = SaleSupplier
        fields = ('id', 'supplier_name', 'supplier_code', 'brand_url', 'main_page', 'contact', 'phone',
                  'mobile', 'fax', 'zip_code', 'email', 'address', 'account_bank', 'account_no', 'progress',
                  'category', 'status', 'created', 'modified', 'memo')


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

    class Meta:
        model = SaleProduct
        fields = (
            'id', 'outer_id', 'title', 'price', 'pic_url', 'product_link', 'sale_supplier', 'contactor',
            'sale_category','platform', 'hot_value', 'sale_price', 'on_sale_price', 'std_sale_price', 
            'memo', 'status','sale_time', 'created', 'modified', 'reserve_time')


class SaleProductSampleSerializer(serializers.ModelSerializer):
    # sale_supplier = SaleSupplierSerializer(read_only=True)
    # sale_category = SaleCategorySerializer()
    status = StatusField()

    class Meta:
        model = SaleProduct
        fields = (
            'id', 'outer_id', 'title', 'price', 'pic_url', 'product_link', 'sale_supplier', 'contactor',
            'sale_category', 'platform', 'hot_value', 'sale_price', 'on_sale_price', 'std_sale_price', 'memo', 'status',
            'sale_time', 'created', 'modified')


