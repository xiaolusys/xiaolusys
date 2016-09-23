# coding: utf-8
from rest_framework import serializers

from flashsale.pay.models import Favorites, Customer

class APISKUSerializer(serializers.Serializer):
    sku_id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    std_sale_price = serializers.SerializerMethodField()
    agent_price = serializers.SerializerMethodField()

    class Meta:
        fields = ('type', 'sku_id', 'name', 'free_num', 'is_saleout', 'std_sale_price', 'agent_price')

    def get_sku_id(self, obj):
        return obj.id

    def get_type(self, obj):
        return obj.type

    def get_name(self, obj):
        return obj.name

    def get_std_sale_price(self, obj):
        return obj.std_sale_price

    def get_agent_price(self, obj):
        return obj.agent_price


class APIProductSerializer(serializers.Serializer):
    sku_items = serializers.SerializerMethodField()
    product_id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    product_img = serializers.SerializerMethodField()
    outer_id = serializers.SerializerMethodField()
    std_sale_price = serializers.SerializerMethodField()
    agent_price = serializers.SerializerMethodField()
    lowest_price = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'type', 'product_id', 'name', 'product_img', 'outer_id', 'is_saleout'
            'std_sale_price', 'agent_price', 'lowest_price', 'sku_items'
        )

    def get_product_id(self, obj):
        return obj.id

    def get_sku_items(self, obj):
        return APISKUSerializer(obj.sku_items(), many=True).data

    def get_type(self, obj):
        return obj.type

    def get_name(self, obj):
        return obj.name

    def get_product_img(self, obj):
        return obj.product_img

    def get_outer_id(self, obj):
        return obj.outer_id

    def get_std_sale_price(self, obj):
        return obj.std_sale_price

    def get_agent_price(self, obj):
        return obj.agent_price

    def get_lowest_price(self, obj):
        return obj.lowest_price


class APIModelProductSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    detail_content = serializers.SerializerMethodField()
    sku_info = serializers.SerializerMethodField()
    comparison = serializers.SerializerMethodField()
    extras = serializers.SerializerMethodField()
    custom_info = serializers.SerializerMethodField()
    teambuy_info = serializers.SerializerMethodField()

    class Meta:
        fields = ('id', 'detail_content', 'sku_info', 'comparison', 'extras', 'custom_info', 'teambuy_info')  #

    def get_id(self, obj):
        return obj.id

    def get_detail_content(self, obj):
        return obj.detail_content

    def get_extras(self, obj):
        return obj.extras.get('saleinfos', {})

    def get_sku_info(self, obj):
        data = APIProductSerializer(obj.get_products(), many=True).data
        sku_ids = [sku['sku_id'] for product in data for sku in product['sku_items']]
        from apis.v1.products import SkustatCtl
        stats = SkustatCtl.multiple(sku_ids)
        stat_map = {stat.id: stat for stat in stats}
        for product in data:
            product['is_saleout'] = True
            for sku in product['sku_items']:
                stat = stat_map[sku['sku_id']]
                sku['free_num'] = stat.get_free_num()
                sku['is_saleout'] = stat.get_free_num() <= 0
                product['is_saleout'] &= sku['is_saleout']
        return data

    def get_custom_info(self, obj):
        request = self.context['request']
        if not request.user.is_authenticated():
            return {'is_favorite': False}
        customer = Customer.objects.filter(user=request.user).first()
        if not customer:
            return {'is_favorite': False}
        favorite = Favorites.objects.filter(customer=customer, model_id=obj.id)
        return {'is_favorite': favorite and True or False}

    def get_teambuy_info(self, obj):
        if not obj.is_teambuy:
            return {'teambuy': False}
        return {
            'teambuy': True,
            'teambuy_price': obj.teambuy_price,
            'teambuy_person_num': obj.teambuy_person_num
        }

    def get_comparison(self, obj):
        return obj.comparison


class APIModelProductListSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    category_id = serializers.SerializerMethodField()
    lowest_agent_price = serializers.SerializerMethodField()
    lowest_std_sale_price = serializers.SerializerMethodField()
    onshelf_time = serializers.SerializerMethodField()
    offshelf_time = serializers.SerializerMethodField()
    is_saleout = serializers.SerializerMethodField()
    sale_state = serializers.SerializerMethodField()
    head_img = serializers.SerializerMethodField()
    web_url = serializers.SerializerMethodField()
    watermark_op = serializers.SerializerMethodField()

    class Meta:
        fields = ('id', 'name', 'category_id', 'lowest_agent_price', 'lowest_std_sale_price',
                  'onshelf_time', 'offshelf_time', 'is_saleout', 'sale_state',
                  'head_img', 'web_url', 'watermark_op')

    def get_id(self, obj):
        return obj.id

    def get_name(self, obj):
        return obj.detail_content['name']

    def get_category_id(self, obj):
        return obj.detail_content['category']['id']

    def get_lowest_agent_price(self, obj):
        return obj.detail_content['lowest_agent_price']

    def get_lowest_std_sale_price(self, obj):
        return obj.detail_content['lowest_std_sale_price']

    def get_onshelf_time(self, obj):
        return obj.detail_content['onshelf_time']

    def get_offshelf_time(self, obj):
        return obj.detail_content['offshelf_time']

    def get_is_saleout(self, obj):
        from apis.v1.products import SkustatCtl
        sku_ids = [sku.id for product in obj.get_products() for sku in product.sku_items()]
        if len(sku_ids) > 1:
            skustat = SkustatCtl.retrieve(sku_ids.pop(0))
            if skustat and not skustat.is_saleout():
                return False

        stats = SkustatCtl.multiple(sku_ids)
        for stat in stats:
            if stat and not stat.is_saleout():
                return False
        return True

    def get_sale_state(self, obj):
        return obj.detail_content['sale_state']

    def get_head_img(self, obj):
        if obj.detail_content['head_imgs']:
            return obj.detail_content['head_imgs'][0]
        return ''

    def get_web_url(self, obj):
        return obj.detail_content['web_url']

    def get_watermark_op(self, obj):
        return obj.detail_content['watermark_op']


class APIMamaProductListSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    cid = serializers.SerializerMethodField()
    pic_path = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    lowest_std_sale_price = serializers.SerializerMethodField()
    lowest_agent_price = serializers.SerializerMethodField()
    sale_num = serializers.SerializerMethodField()

    level_info = serializers.SerializerMethodField()
    shop_products_num = serializers.SerializerMethodField()
    sale_num_desc = serializers.SerializerMethodField()
    rebet_amount_desc = serializers.SerializerMethodField()
    next_rebet_amount_desc = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'cid',
            'pic_path',
            'name',
            'lowest_std_sale_price',
            'lowest_agent_price',
            'shop_products_num',
            'sale_num',
            'sale_num_desc',
            'rebet_amount',
            'rebet_amount_desc',
            'next_rebet_amount_desc',
            'next_rebet_amount',
            'level_info'
        )

    def get_id(self, obj):
        return obj.id

    def get_cid(self, obj):
        return obj.detail_content['category']['id']

    def get_name(self, obj):
        return obj.detail_content['name']

    def get_lowest_agent_price(self, obj):
        return obj.detail_content['lowest_agent_price']

    def get_lowest_std_sale_price(self, obj):
        return obj.detail_content['lowest_std_sale_price']

    def get_pic_path(self, obj):
        if obj.detail_content['head_imgs']:
            return obj.detail_content['head_imgs'][0]
        return ''

    def get_sale_num(self, obj):
        return obj.sale_num

    def get_level_info(self, obj):
        mama = self.context['mama']
        next_agencylevel, next_agencylevel_desc = mama.next_agencylevel_info()
        info = {
            "agencylevel_desc": mama.get_agencylevel_display(),
            "agencylevel": mama.agencylevel,
            "next_agencylevel": next_agencylevel,
            "next_agencylevel_desc": next_agencylevel_desc
        }
        return info

    def get_shop_products_num(self, obj):
        shop_products_num = self.context['shop_product_num']
        return shop_products_num

    def get_sale_num_desc(self, obj):
        return u'{0}人在卖'.format(obj.sale_num)

    def get_rebet_amount_desc(self, obj):
        return u'佣{0}￥'.format(obj.rebet_amount)

    def get_next_rebet_amount_desc(self, obj):
        return u'佣{0}￥'.format(obj.next_rebet_amount)


