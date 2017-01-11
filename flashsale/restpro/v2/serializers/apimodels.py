# coding: utf-8
from rest_framework import serializers

from flashsale.pay.models import Favorites, Customer
from flashsale.pay.models.product import ModelProduct


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
    elite_score = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'type', 'product_id', 'name', 'product_img', 'outer_id', 'is_saleout'
            'std_sale_price', 'agent_price', 'lowest_price', 'sku_items', 'elite_score'
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

    def get_elite_score(self, obj):
        if hasattr(obj, 'elite_score'):
            return obj.elite_score
        return 0


class APIModelProductSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    sku_info = serializers.SerializerMethodField()
    detail_content = serializers.SerializerMethodField()
    comparison = serializers.SerializerMethodField()
    extras = serializers.SerializerMethodField()
    custom_info = serializers.SerializerMethodField()
    teambuy_info = serializers.SerializerMethodField()
    buy_coupon_url = serializers.SerializerMethodField()

    class Meta:
        fields = ('id', 'detail_content', 'sku_info', 'comparison', 'extras', 'custom_info', 'teambuy_info', 'buy_coupon_url')  #

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
        model_saleout = True
        for product in data:
            product['is_saleout'] = True
            for sku in product['sku_items']:
                stat = stat_map[sku['sku_id']]
                sku['free_num'] = stat.get_free_num()
                sku['is_saleout'] = stat.get_free_num() <= 0
                product['is_saleout'] &= sku['is_saleout']
            model_saleout &= product['is_saleout']

        obj.detail_content['is_sale_out'] = model_saleout
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

    def get_buy_coupon_url(self, obj):
        # type: (ModuleProduct) -> text_type
        """如果该款式是精品商品 则返回 对应的 购券 app 协议跳转链接
        """
        if not (obj.detail_content['is_boutique'] and obj.detail_content['product_type'] == 0):
            return ''

        payinfo = obj.extras.get('payinfo')
        if not payinfo:
            return ''
        coupon_template_ids = payinfo.get('coupon_template_ids')
        if not coupon_template_ids:
            return ''

        templateid = coupon_template_ids[0]
        virtual_model_products = ModelProduct.objects.get_virtual_modelproducts()  # 虚拟商品
        find_mp = None
        for md in virtual_model_products:
            md_bind_tpl_id = md.extras.get('template_id')
            if not md_bind_tpl_id:
                continue
            if templateid == md_bind_tpl_id:
                find_mp = md
                break
        if not find_mp:
            return ''

        protocol = 'com.jimei.xlmm://app/v1/webview?is_native=1&url={0}'
        url = 'https://m.xiaolumeimei.com/mall/buycoupon?modelid={0}'.format(find_mp.id)
        return protocol.format(url)


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
    elite_score = serializers.SerializerMethodField()

    class Meta:
        fields = ('id', 'name', 'category_id', 'lowest_agent_price', 'lowest_std_sale_price',
                  'onshelf_time', 'offshelf_time', 'is_saleout', 'sale_state',
                  'head_img', 'web_url', 'watermark_op', 'elite_score')

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
        head_img = obj.detail_content.get('head_img')
        if not head_img:
            head_img = obj.detail_content['head_imgs'] and obj.detail_content['head_imgs'][0] or ''
        return head_img

    def get_web_url(self, obj):
        return obj.detail_content['web_url']

    def get_watermark_op(self, obj):
        return obj.detail_content['watermark_op']

    def get_elite_score(self, obj):
        return obj.sku_info[0]['elite_score']


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
    is_boutique = serializers.SerializerMethodField()
    elite_level_prices = serializers.SerializerMethodField()

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
            'level_info',
            'is_boutique',
            'elite_level_prices'
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
        head_img = obj.detail_content.get('head_img')
        if not head_img:
            head_img = obj.detail_content['head_imgs'] and obj.detail_content['head_imgs'][0] or ''
        return head_img

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
        return u'佣￥{0}'.format(obj.rebet_amount)

    def get_next_rebet_amount_desc(self, obj):
        return u'佣￥{0}'.format(obj.next_rebet_amount)

    def get_is_boutique(self, obj):
        return obj.detail_content['is_boutique']

    def get_elite_level_prices(self, obj):
        """下个 精品汇积分 等级 价格
        """
        if not obj.detail_content['is_boutique']:
            return {}
        mama = self.context['mama']
        if not mama:
            return {}
        try:
            templateid = obj.extras['payinfo']['coupon_template_ids'][0]
        except:
            return {}
        find_mp = None
        virtual_model_products = ModelProduct.objects.get_virtual_modelproducts()  # 虚拟商品
        for md in virtual_model_products:
            md_bind_tpl_id = md.extras.get('template_id')
            if not md_bind_tpl_id:
                continue
            if templateid == md_bind_tpl_id:
                find_mp = md
                break
        item = {'elite_level_price': '', 'next_elite_level_price': ''}
        for product in find_mp.products:
            if mama.elite_level in product.name:
                item['elite_level_price'] = '￥%s' % product.agent_price
            elif mama.next_elite_level in product.name:
                item['next_elite_level_price'] = '升级后￥%s' % product.agent_price
        return item
