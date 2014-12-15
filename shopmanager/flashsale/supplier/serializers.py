from models import SaleSupplier, SaleCategory, SaleProduct
from rest_framework import serializers
from rest_framework.pagination import PaginationSerializer


class SaleSupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleSupplier
        fields = ('id','supplier_name','supplier_code','brand_url','main_page','contact','phone',
                  'mobile','fax','zip_code','email','address','account_bank','account_no',
                  'created','modified')


class PaginatedSaleSupplierSerializer(PaginationSerializer):
    class Meta:
        object_serializer_class = SaleSupplierSerializer


class SaleCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleCategory
        fields = ('id','name','created','modified')


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
    sale_category = SaleCategorySerializer(read_only=True)
    status = StatusField()
    class Meta:
        model = SaleProduct
        fields = ('id','outer_id','title','price','pic_url','product_link','sale_supplier',
                  'sale_category','platform','hot_value','sale_price','memo','status','created','modified')


class PaginatedSaleProductSerializer(PaginationSerializer):
    class Meta:
        object_serializer_class = SaleProductSerializer
