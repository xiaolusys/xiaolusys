from rest_framework import serializers
from .models import Product, ProductSku, Item, ProductLocation
from shopback.archives.models import DepositeDistrict
from shopback.categorys.models import Category
from shopback.users.models import User
from flashsale.pay.models import ModelProduct, ModelProductSkuContrast
from pms.supplier.serializers import SaleProductSerializer


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


class ProductListSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    barcode = serializers.CharField(source='BARCODE', read_only=True)
    status = serializers.CharField(source='get_status_display', read_only=True)
    sale_category = serializers.SerializerMethodField(read_only=True)
    category = serializers.CharField()
    sku_extras = serializers.SerializerMethodField(read_only=True)
    # skus = serializers.SerializerMethodField()
    name = serializers.CharField()
    created = serializers.DateTimeField()
    type = serializers.CharField()
    pic_path = serializers.CharField()
    model_id = serializers.CharField()
    ref_link = serializers.CharField(allow_blank=True)
    memo = serializers.CharField(allow_blank=True, required=False)
    outer_id = serializers.CharField()
    price_dict = serializers.SerializerMethodField()
    stock_dict = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'sale_category', 'created', 'sku_extras', 'type', 'pic_path', 'ref_link',
                  'memo', 'status', 'barcode', 'model_id', 'outer_id', 'price_dict', 'stock_dict')

    def get_price_dict(self, obj):
        return {
            'cost': obj.cost,
            'std_purchase_price': obj.std_purchase_price,
            'std_sale_price': obj.std_sale_price,
            'agent_price': obj.agent_price,
            'staff_price': obj.staff_price,
        }

    def get_stock_dict(self, obj):
        return obj.get_stock_dict()

    def get_sale_category(self, obj):
        category = obj.category.get_sale_category()
        from pms.supplier.serializers import SaleCategorySerializer
        return SaleCategorySerializer(category).data

    def get_sku_extras(self, obj):
        return obj.sku_extras_info


class ProductEditSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    barcode = serializers.CharField(source='BARCODE', read_only=True)
    status = serializers.CharField(source='get_status_display', read_only=True)
    sale_category = serializers.SerializerMethodField(read_only=True)
    category = serializers.CharField()
    sku_extras = serializers.SerializerMethodField(read_only=True)
    # skus = serializers.SerializerMethodField()
    name = serializers.CharField()
    created = serializers.DateTimeField()
    type = serializers.CharField()
    pic_path = serializers.CharField()
    model_id = serializers.CharField()
    ref_link = serializers.CharField(allow_blank=True)
    memo = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'sale_category', 'created', 'sku_extras', 'type', 'pic_path', 'ref_link', 'memo', 'status', 'barcode', 'model_id')

    def get_sale_category(self, obj):
        category = obj.category.get_sale_category()
        from pms.supplier.serializers import SaleCategorySerializer
        return SaleCategorySerializer(category).data

    def get_sku_extras(self, obj):
        return obj.sku_extras_info

    def save(self, product_id=None):
        from pms.supplier.models import SaleCategory
        try:
            content = self.data
            name = content['name']
            sale_category = content['category']
            product_category = SaleCategory.objects.get(id=sale_category).get_product_category()
            type = content['type']
            pic_path = content['pic_path']
            ref_link = content['ref_link']
            memo = content['memo']
            skus = content['sku_extras']
            if product_id:
                product = Product.objects.get(id=product_id)
                product.name = name
                product.product_category = product_category
                product.type = type
                product.pic_path = pic_path
                product.ref_link = ref_link
                product.memo = memo
                product.save()
                product.update_skus(skus)
            else:
                product = Product.create(name, product_category, type, pic_path,
                       ref_link, memo, skus)
            return product
        except Exception, e:
            raise e


class UpdateProductSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    barcode = serializers.CharField(source='BARCODE', read_only=True)
    status = serializers.CharField(source='get_status_display', read_only=True)
    sale_category = serializers.SerializerMethodField(read_only=True)
    category = serializers.CharField()
    sku_extras = serializers.SerializerMethodField(read_only=True)
    name = serializers.CharField()
    type = serializers.CharField()
    pic_path = serializers.CharField()
    ref_link = serializers.CharField(allow_blank=True)
    memo = serializers.CharField(allow_blank=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'sale_category', 'sku_extras', 'type', 'pic_path', 'ref_link', 'memo', 'status', 'barcode', )

    def get_sale_category(self, obj):
        category = obj.category.get_sale_category()
        from pms.supplier.serializers import SaleCategorySerializer
        return SaleCategorySerializer(category).data

    def get_sku_extras(self, obj):
        return obj.sku_extras_info

    def save(self, product_id=None):
        from pms.supplier.models import SaleCategory
        try:
            content = self.data
            name = content['name']
            sale_category = content['category']
            product_category = SaleCategory.objects.get(id=sale_category).get_product_category()
            type = content['type']
            pic_path = content['pic_path']
            ref_link = content['ref_link']
            memo = content['memo']
            skus = content['sku_extras']
            if product_id:
                product = Product.objects.get(id=product_id)
                product.name = name
                product.product_category = product_category
                product.type = type
                product.pic_path = pic_path
                product.ref_link = ref_link
                product.memo = memo
                product.save()
                product.update_skus(skus)
            else:
                product = Product.create(name, product_category, type, pic_path,
                       ref_link, memo, skus)
            return product
        except Exception, e:
            raise e


class CreateProductSerializer(serializers.Serializer):
    sku_extras = serializers.ListField()
    name = serializers.CharField()
    category = serializers.CharField()
    type = serializers.CharField()
    pic_path = serializers.CharField()
    ref_link = serializers.CharField(allow_blank=True)
    memo = serializers.CharField(allow_blank=True, required=False)

    def save(self, product_id=None):
        from pms.supplier.models import SaleCategory
        content = self.data
        name = content['name']
        sale_category = content['category']
        product_category = SaleCategory.objects.get(id=sale_category).get_product_category()
        type = content['type']
        pic_path = content['pic_path']
        ref_link = content['ref_link']
        memo = content.get('memo', '')
        skus = content['sku_extras']
        if product_id:
            product = Product.objects.get(id=product_id)
            product.name = name
            product.category = product_category
            product.type = type
            product.pic_path = pic_path
            product.ref_link = ref_link
            product.memo = memo
            product.save()
            product.update_skus(skus)
        else:
            product = Product.create(name, product_category, type, pic_path,
                   ref_link, memo, skus)
        return product


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
                  'is_boutique',
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
            'content_imgs',
            'salecategory',
            'saleproduct',
            'extras',
            'is_teambuy',
            'teambuy_price',
            'teambuy_person_num',
            'is_boutique',
            'product_type',
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
        exclude = ()
