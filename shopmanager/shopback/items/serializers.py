from rest_framework import serializers
from .models import Product, ProductSku, Item, ProductLocation
from shopback.archives.models import DepositeDistrict
from shopback.categorys.models import Category
from shopback.users.models import User
from flashsale.pay.models import ModelProduct, ModelProductSkuContrast
from supplychain.supplier.serializers import SaleProductSerializer


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


class ItemProductSkuSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='product.name', read_only=True)
    color = serializers.SerializerMethodField()
    color_id = serializers.IntegerField(source='product.id', read_only=True)

    class Meta:
        model = ProductSku
        fields = (
            "id",
            "color_id",
            "outer_id",
            "barcode",
            "quantity",
            "warn_num",
            "remain_num",
            "wait_post_num",
            "sale_num",
            "reduce_num",
            "cost",
            "std_sale_price",
            "agent_price",
            "properties_name",
            "properties_alias",
            "created",
            "modified",
            "status",
            "memo",
            "name",
            "color"
        )

    def get_color(self, obj):
        return obj.product.name.split('/')[-1]


class ModelProductSerializer(serializers.ModelSerializer):
    skus = serializers.SerializerMethodField()
    saleproduct_id = serializers.ReadOnlyField()

    class Meta:
        model = ModelProduct
        fields = ('id',
                  'name',
                  'head_imgs',
                  'content_imgs',
                  'salecategory',
                  'lowest_agent_price',
                  'lowest_std_sale_price',
                  'is_onsale',
                  'is_teambuy',
                  'is_recommend',
                  'is_topic',
                  'is_flatten',
                  'is_watermark',
                  'teambuy_price',
                  'teambuy_person_num',
                  'shelf_status',
                  'onshelf_time',
                  'offshelf_time',
                  'order_weight',
                  'rebeta_scheme_id',
                  'saleproduct_id',
                  'extras',
                  'status',
                  'created',
                  'skus')

    def get_skus(self, obj):
        """ skus """
        products = obj.products
        product_sku_ids = []
        for product in products:
            product_skus = product.pskus
            for product_sku in product_skus:
                product_sku_ids.append(product_sku)
        return ItemProductSkuSerializer(product_sku_ids, many=True).data


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


class ModelProductSkuContrastSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelProductSkuContrast
