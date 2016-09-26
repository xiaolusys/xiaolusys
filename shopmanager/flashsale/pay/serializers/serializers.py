# -*- encoding:utf-8 -*-
from django.forms import model_to_dict
from rest_framework import serializers

from shopback.items.models import Product, ProductSku
from ..models import SaleTrade, District, UserAddress, ModelProduct, BrandProduct


class DetailInfoField(serializers.Field):
    def to_representation(self, obj):

        detail_dict = {'head_imgs': [], 'content_imgs': [],
                       'buy_limit': obj.buy_limit,
                       'per_limit': obj.per_limit}
        if obj.head_imgs.strip():
            detail_dict['head_imgs'] = [s.strip() for s in obj.head_imgs.split('\n')
                                        if s.startswith('http://') or s.startswith('https://')]

        if obj.content_imgs.strip():
            detail_dict['content_imgs'] = [s.strip() for s in obj.content_imgs.split('\n')
                                           if s.startswith('http://') or s.startswith('https://')]

        return detail_dict

    def to_internal_value(self, data):
        return data


class CusUidField(serializers.Field):
    def to_representation(self, obj):
        return obj.cus_uid

    def to_internal_value(self, data):
        return data


class ProductSerializer(serializers.ModelSerializer):
    #     category = SaleCategorySerializer()
    class Meta:
        model = Product
        fields = ('id', 'name', 'title', 'category', 'pic_path', 'collect_num', 'std_sale_price',
                  'agent_price', 'sale_out', 'status', 'created', 'memo')


class ProductSkuField(serializers.Field):
    def to_representation(self, obj):
        sku_list = []
        for sku in obj.filter(status=ProductSku.NORMAL):
            sku_dict = model_to_dict(sku)
            sku_dict['sale_out'] = sku.sale_out
            sku_list.append(sku_dict)

        return sku_list

    def to_internal_value(self, data):
        return data


class ProductDetailSerializer(serializers.ModelSerializer):
    #    category = SaleCategorySerializer()
    details = DetailInfoField()
    prod_skus = ProductSkuField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'pic_path', 'collect_num', 'std_sale_price',
                  'agent_price', 'status', 'created', 'memo', 'prod_skus', 'details')


class SaleOrderField(serializers.Field):
    def to_representation(self, obj):
        order_list = []
        for order in obj.all():
            odict = model_to_dict(order)
            odict['refund'] = order.refund
            odict['refundable'] = order.refundable
            order_list.append(odict)
        return order_list

    def to_internal_value(self, data):
        return data


class SaleTradeSerializer(serializers.ModelSerializer):
    #    category = SaleCategorySerializer()
    sale_orders = SaleOrderField()

    class Meta:
        model = SaleTrade
        fields = ('id', 'tid', 'buyer_id', 'buyer_nick', 'channel', 'payment', 'post_fee', 'total_fee', 'channel',
                  'payment', 'post_fee', 'total_fee', 'buyer_message', 'seller_memo', 'created', 'pay_time',
                  'modified', 'consign_time', 'trade_type', 'out_sid', 'logistics_company', 'receiver_name',
                  'receiver_state', 'receiver_city', 'receiver_district', 'receiver_address', 'receiver_zip',
                  'receiver_mobile', 'receiver_phone', 'status', 'status_name', 'sale_orders', 'order_num', 'order_type')


class SampleSaleTradeSerializer(serializers.ModelSerializer):
    #    category = SaleCategorySerializer()

    class Meta:
        model = SaleTrade
        fields = ('id', 'tid', 'buyer_id', 'buyer_nick', 'channel', 'payment', 'post_fee', 'total_fee', 'channel',
                  'payment', 'post_fee', 'total_fee', 'buyer_message', 'seller_memo', 'created', 'pay_time',
                  'modified', 'consign_time', 'trade_type', 'out_sid', 'logistics_company', 'receiver_name',
                  'receiver_state', 'receiver_city', 'receiver_district', 'receiver_address', 'receiver_zip',
                  'receiver_mobile', 'receiver_phone', 'status', 'status_name', 'order_num', 'order_title',
                  'order_pic')


class UserAddressSerializer(serializers.ModelSerializer):
    #    category = SaleCategorySerializer()
    class Meta:
        model = UserAddress
        fields = ('id', 'cus_uid', 'receiver_name', 'receiver_state', 'receiver_city', 'receiver_district',
                  'receiver_address', 'receiver_zip', 'receiver_mobile', 'receiver_phone', 'default')


# 用户积分Serializer
from ..models import IntegralLog, Integral


class UserIntegralSerializer(serializers.ModelSerializer):
    class Meta:
        model = Integral
        fields = ('id', 'integral_user', 'integral_value')


class UserIntegralLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegralLog
        fields = \
            ('id', 'integral_user', 'mobile', 'order', 'log_value', 'log_status', 'log_type', 'in_out', 'created',
             'modified')

class ModelProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelProduct
        fields = ('id', 'name', 'head_imgs', 'content_imgs', 'sale_time')
        # , 'std_sale_price', 'agent_price', 'shelf_status', 'status')


class BrandProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandProduct
        fields = ('id', 'model_id', 'product_name', 'product_img', 'location_id', 'pic_type', 'jump_url')
