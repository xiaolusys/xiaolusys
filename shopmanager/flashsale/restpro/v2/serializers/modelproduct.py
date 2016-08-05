# coding: utf-8

import urlparse
import datetime

from django.conf import settings
from rest_framework import serializers

from flashsale.pay.models import ModelProduct
from shopback.items.models import Product
from flashsale.restpro.local_cache import image_watermark_cache

class SimpleModelProductSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(view_name='rest_v2:modelproduct-detail')
    category_id = serializers.IntegerField(source='salecategory.id', read_only=True)
    is_saleout  = serializers.BooleanField(source='is_sale_out',read_only=True)
    sale_state  = serializers.SerializerMethodField(read_only=True)
    web_url     = serializers.SerializerMethodField(read_only=True)
    watermark_op = serializers.SerializerMethodField(read_only=True)
    is_favorite = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ModelProduct
        fields = ('id', 'url', 'name', 'category_id', 'lowest_agent_price', 'lowest_std_sale_price',
                  'is_saleout', 'is_favorite', 'sale_state', 'head_img', 'web_url', 'watermark_op')

    def get_sale_state(self, obj):
        if obj.shelf_status == obj.OFF_SHELF and \
                (not obj.onshelf_time or obj.onshelf_time > datetime.datetime.now()):
            return 'will'
        return obj.shelf_status

    def get_web_url(self, obj):
        return urlparse.urljoin(settings.M_SITE_URL, Product.MALL_PRODUCT_TEMPLATE_URL.format(obj.id))

    def get_watermark_op(self, obj):
        if not obj.is_watermark:
            return ''
        return image_watermark_cache.latest_qs or ''

    def get_is_favorite(self, obj):
        return False


class ModelProductSerializer(serializers.ModelSerializer):

    detail_content = serializers.SerializerMethodField()
    extras = serializers.SerializerMethodField()
    sku_info = serializers.SerializerMethodField()
    class Meta:
        model = ModelProduct
        fields = ('id', 'detail_content', 'sku_info', 'comparison', 'extras') #

    def get_detail_content(self, obj):
        content = obj.detail_content
        if obj.is_flatten:
            request = self.context.get('request')
            product_id = request.GET.get('product_id', None)
            if product_id and product_id.isdigit():
                product = obj.products.filter(id=product_id).first()
                content['name'] = product.name
                content['head_imgs'] = [product.pic_path]
        return content

    def get_extras(self, obj):
        return obj.extras.get('saleinfos',{})

    def get_sku_info(self, obj):
        if obj.is_flatten:
            request = self.context.get('request')
            product_id = request.GET.get('product_id',None)
            if  product_id and product_id.isdigit():
                product = obj.products.filter(id=product_id).first()
                return obj.product_simplejson(product)
        return obj.sku_info