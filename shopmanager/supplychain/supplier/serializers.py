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
from django.contrib.auth.models import User
from shopback.warehouse import WARE_NONE, WARE_GZ, WARE_SH, WARE_CHOICES


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
    figures = SupplierFigureSerializer(read_only=True)
    zone_name = serializers.CharField(source='zone.name', read_only=True)

    class Meta:
        model = SaleSupplier
        fields = ('id',
                  'supplier_name',
                  'supplier_code',
                  'brand_url',
                  "product_link",
                  'total_sale_num',
                  "description",
                  'progress',
                  "mobile",
                  'category',
                  "address",
                  'status',
                  'created',
                  'modified',
                  'memo',
                  'figures',
                  'zone_name',
                  'get_ware_by_display')


class SaleSupplierFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleSupplier
        fields = ("supplier_name",
                  "supplier_code",
                  "description",
                  "brand_url",
                  "main_page",
                  "product_link",
                  "platform",
                  "category",
                  "speciality",
                  "contact",
                  "phone",
                  "mobile",
                  "fax",
                  "zip_code",
                  "email",
                  "address",
                  "account_bank",
                  "account_no",
                  "memo",
                  "status",
                  "progress",
                  "supplier_type",
                  "supplier_zone",
                  "buyer",
                  "ware_by")

    def validate(self, data):
        """
        """
        if data.has_key('mobile') and (data['mobile'] == None or data['mobile'] == u''):
            raise serializers.ValidationError("手机号不能为空!")
        if data.has_key('contact') and (data['contact'] == None or data['contact'] == u''):
            raise serializers.ValidationError("联系人不能为空!")
        return data

    def validate_supplier_name(self, value):
        """
        #  validate_<model 的字段>  这中写法对该字段进行校验
        supplier_name　检查供应商名称字段
        """
        if None == value or value.isdigit():
            raise serializers.ValidationError("供应商名称不能为纯数字!")
        return value

    def validate_supplier_type(self, value):
        t = [x[0] for x in self.Meta.model.SUPPLIER_TYPE]
        if value not in t:
            raise serializers.ValidationError("供应商类型错误!")
        return value

    def validate_ware_by(self, value):
        t = [x[0] for x in WARE_CHOICES]
        if value not in t:
            raise serializers.ValidationError("仓库选择错误!")
        return value


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
    orderlist_show_memo = serializers.NullBooleanField()

    class Meta:
        model = SaleProduct
        fields = (
            'id', 'outer_id', 'title', 'price', 'pic_url', 'product_link', 'sale_supplier', 'contactor',
            'sale_category', 'platform', 'hot_value', 'sale_price', 'on_sale_price', 'std_sale_price',
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
            'sale_category', 'platform', 'hot_value', 'sale_price', 'on_sale_price', 'std_sale_price',
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
            'id', 'outer_id', 'title', 'price', 'pic_url', 'product_link', 'status', 'sale_supplier', 'contactor',
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
    supplier_name = serializers.CharField(source='sale_product.sale_supplier.supplier_name', read_only=True)
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
    reference_username = serializers.SerializerMethodField('reference_user_name', read_only=True)
    photo_username = serializers.SerializerMethodField('photo_user_name', read_only=True)

    class Meta:
        model = SaleProductManageDetail
        fields = (
            'id', 'supplier_id', 'sale_product_id', 'product_name', 'product_pic', 'product_link', 'design_person',
            'order_weight', 'model_id', 'supplier_name',
            'sale_category', 'material_status', 'today_use_status', 'product_purchase_price', 'product_sale_price',
            'product_origin_price', 'design_take_over', 'design_complete', 'is_approved', 'is_promotion',
            'reference_username', 'photo_username',
            'created', 'modified')

    def reference_user_name(self, obj):
        """ 资料录入人 """
        try:
            woker = User.objects.get(id=obj.reference_user)
            full_name = ''.join([woker.last_name, woker.first_name])
            return full_name if full_name else woker.username
        except User.DoesNotExist:
            return ''

    def photo_user_name(self, obj):
        """ 平面制作人 """
        try:
            woker = User.objects.get(id=obj.photo_user)
            full_name = ''.join([woker.last_name, woker.first_name])
            return full_name if full_name else woker.username
        except User.DoesNotExist:
            return ''


class ManageDetailAssignWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleProductManageDetail
        fields = ('id', 'reference_user', 'photo_user', 'modified')


class SaleProductManageDetailSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleProductManageDetail

