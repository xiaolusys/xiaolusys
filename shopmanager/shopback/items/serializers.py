from rest_framework import serializers
from .models import Product, ProductSku, Item, ProductLocation
from shopback.archives.models import DepositeDistrict
from shopback.categorys.models import Category
from shopback.users.models import User
from flashsale.pay.models import ModelProduct


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('cid', 'parent_cid', 'name', 'status', 'sort_order')


class ProductSkuSerializer(serializers.ModelSerializer):
    barcode = serializers.CharField(source='BARCODE', read_only=True)
    districts = serializers.CharField(source='get_district_list', read_only=True)

    class Meta:
        model = ProductSku
        # fields =  ('cid','parent_cid' ,'is_parent' ,'name','status','sort_order')
        # fields = ('parent_cid' ,'is_parent' )
        exclude = ('created',)


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    barcode = serializers.CharField(source='BARCODE', read_only=True)
    districts = serializers.CharField(source='get_district_list', read_only=True)
    status = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Product
        # fields =  ('cid','parent_cid' ,'is_parent' ,'name','status','sort_order')
        # fields = ('parent_cid' ,'is_parent' )
        exclude = ('created',)


class ProductItemSerializer(serializers.ModelSerializer):
    """ docstring for ProductItem ModelResource """

    class Meta:
        model = Item
        # fields = ('id','outer_id','name','outer_sku_id','properties_name','price','num')
        exclude = ('desc',)


class ProductLocationSerializer(serializers.ModelSerializer):
    district = serializers.CharField(source='district.district_no', read_only=True)

    class Meta:
        model = ProductLocation
        fields = ("product_id", "sku_id", "outer_id", "name", "outer_sku_id", "properties_name", "district")
        # exclude = ('district',)


class DepositeDistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositeDistrict
        fields = ("district_no", "parent_no", "location", "in_use", "extra_info")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # fields=("district_no","parent_no","location","in_use","extra_inf")
        exclude = ('created_at',)


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        # fields=("district_no","parent_no","location","in_use","extra_inf")
        exclude = ('desc',)


class ModelProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelProduct


class ModelProductUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelProduct
        fields = (
            'id',
            'name',
            'head_imgs',
            'salecategory',
            'saleproduct',
            'extras',
            'is_teambuy',
            'teambuy_price',
            'teambuy_person_num',
            'status'
        )


class ProductUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'outer_id',
            'model_id',
            'sale_charger',
            'category',
            'remain_num',
            'cost',
            'agent_price',
            'std_sale_price',
            'ware_by',
            'pic_path',
            'sale_product',
        )


class ProductSkuUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSku
        fields = (
            'id',
            'outer_id',
            'product',
            'remain_num',
            'cost',
            'std_sale_price',
            'agent_price',
            'properties_name',
            'properties_alias',
            'barcode'
        )