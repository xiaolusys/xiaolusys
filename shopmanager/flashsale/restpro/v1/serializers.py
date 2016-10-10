# coding=utf-8
import datetime
import os
import random
from django.conf import settings
from django.template import Context, Template

from flashsale.xiaolumm.models.models_advertis import MamaVebViewConf
from rest_framework import serializers

from flashsale.coupon.models import OrderShareCoupon
from flashsale.pay.models import BrandEntry, BrandProduct
from flashsale.pay.models import (
    SaleTrade,
    SaleOrder,
    SaleRefund,
    Productdetail,
    ModelProduct,
    ShoppingCart,
    Customer,
    Register,
    GoodShelf,
    CustomShare,
    UserBudget,
    IntegralLog,
    Integral
)
from flashsale.pay.models.favorites import Favorites
from flashsale.promotion.models import ActivityEntry, ActivityProduct
from shopback.items.models import Product, ProductSku
from shopback.categorys.models import ProductCategory
from shopback.logistics.models import LogisticsCompany
from shopback.trades.models import TradeWuliu, PackageOrder, ReturnWuLiu
from flashsale.xiaolumm.models import XiaoluMama, PotentialMama, ReferalRelationship
from rest_framework import serializers
from flashsale.restpro import constants
from flashsale.xiaolumm.models.models_advertis import MamaVebViewConf
from flashsale.xiaolumm import util_emoji
from flashsale.coupon.models import OrderShareCoupon

from flashsale.xiaolumm.models.models_lesson import (
    LessonTopic,
    Instructor,
    Lesson,
    LessonAttendRecord,
)


class RegisterSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Register
        fields = ('id', 'vmobile')


class XiaoluMamaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = XiaoluMama
        fields = ('id', 'cash', 'agencylevel', 'created', 'status')


class UserBudgetSerialize(serializers.HyperlinkedModelSerializer):
    budget_cash = serializers.FloatField(source='get_amount_display', read_only=True)
    is_cash_out = serializers.IntegerField(source='is_could_cashout', read_only=True)
    cash_out_limit = serializers.SerializerMethodField()

    class Meta:
        model = UserBudget
        fields = ('budget_cash', 'is_cash_out', 'cash_out_limit')

    def get_cash_out_limit(self, obj):
        """ 设置提现限制 """
        return 2.0


class CustomerSerializer(serializers.HyperlinkedModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='rest_v1:customer-detail')
    url = serializers.SerializerMethodField()
    user_id = serializers.CharField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    xiaolumm = XiaoluMamaSerializer(source='get_charged_mama', read_only=True)
    user_budget = UserBudgetSerialize(source='getBudget', read_only=True)
    has_usable_password = serializers.BooleanField(source='user.has_usable_password', read_only=True)
    has_password = serializers.BooleanField(source='has_user_password', read_only=True)
    is_attention_public = serializers.IntegerField(source='is_attention_wx_public', read_only=True)
    # nick = serializers.CharField(read_only=False)

    score = serializers.SerializerMethodField()
    coupon_num = serializers.IntegerField(source='get_coupon_num', read_only=True)
    waitpay_num = serializers.IntegerField(source='get_waitpay_num', read_only=True)
    waitgoods_num = serializers.IntegerField(source='get_waitgoods_num', read_only=True)
    refunds_num = serializers.IntegerField(source='get_refunds_num', read_only=True)

    class Meta:
        model = Customer
        fields = ('id', 'url', 'user_id', 'username', 'nick', 'mobile', 'email', 'phone', 'score',
                  'thumbnail', 'status', 'created', 'modified', 'xiaolumm', 'has_usable_password', 'has_password',
                  'user_budget', 'is_attention_public', 'coupon_num', 'waitpay_num', 'waitgoods_num', 'refunds_num')

    def get_score(self, obj):
        user_integral = Integral.objects.filter(integral_user=obj.id).first()
        if user_integral:
            return user_integral.integral_value
        return 0

    def get_url(self, obj):
        return ''


#####################################################################################
class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ('cid', 'parent_cid', 'name', 'status', 'sort_order')


class ProductSkuSerializer(serializers.ModelSerializer):
    is_saleout = serializers.BooleanField(source='sale_out', read_only=True)

    class Meta:
        model = ProductSku
        fields = ('id', 'outer_id', 'name', 'remain_num', 'size_of_sku', 'is_saleout', 'std_sale_price', 'agent_price')


class JSONParseField(serializers.Field):
    def to_representation(self, obj):
        return obj

    def to_internal_value(self, data):
        return data


class JsonListField(serializers.Field):
    def to_representation(self, obj):
        return [s.strip() for s in obj.split() if s.startswith(('http://', 'https://'))]

    def to_internal_value(self, data):
        return data


class ProductdetailSerializer(serializers.ModelSerializer):
    head_imgs = JsonListField(read_only=True, required=False)
    content_imgs = JsonListField(read_only=True, required=False)

    class Meta:
        model = Productdetail
        fields = ('head_imgs', 'content_imgs', 'mama_discount', 'is_recommend',
                  'buy_limit', 'per_limit', 'mama_rebeta', 'material', 'wash_instructions', 'note', 'color')

class ModelProductSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    head_imgs = JsonListField(read_only=True, required=False)
    content_imgs = JsonListField(read_only=True, required=False)
    is_sale_out = serializers.BooleanField(read_only=True)
    buy_limit = serializers.SerializerMethodField()
    per_limit = serializers.SerializerMethodField()
    class Meta:
        model = ModelProduct
        fields = ('id', 'name', 'head_imgs', 'content_imgs', 'is_sale_out', 'is_flatten', 'buy_limit', 'per_limit')

    def get_buy_limit(self, obj):
        return False

    def get_per_limit(self, obj):
        return 3

class SimpleModelProductSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    is_single_spec = serializers.BooleanField(read_only=True)
    is_sale_out = serializers.BooleanField(read_only=True)
    head_imgs = serializers.SerializerMethodField()
    content_imgs = serializers.SerializerMethodField()
    buy_limit = serializers.SerializerMethodField()
    per_limit = serializers.SerializerMethodField()
    class Meta:
        model = ModelProduct
        fields = ('id', 'name', 'is_single_spec', 'is_sale_out', 'head_imgs', 'content_imgs', 'is_flatten', 'buy_limit', 'per_limit')

    def get_buy_limit(self, obj):
        return False

    def get_per_limit(self, obj):
        return 3

    def get_head_imgs(self, obj):
        return []

    def get_content_imgs(self, obj):
        return []

class ActivityProductSerializer(serializers.ModelSerializer):

    web_url = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = ActivityProduct
        fields = ('id', 'product_id', 'model_id', 'product_name', 'product_img',
                  'product_lowest_price', 'product_std_sale_price', 'web_url')

    def get_web_url(self, obj):
        if obj.product:
            return obj.product.get_weburl()
        return ''

class ActivityEntrySerializer(serializers.ModelSerializer):

    products = ActivityProductSerializer(source='activity_products', many=True)
    extras = JSONParseField(read_only=True, required=False)
    class Meta:
        model = ActivityEntry
        fields = ('id', 'title', 'login_required', 'act_desc', 'act_img', 'act_logo', 'mask_link', 'act_link',
                  'act_type', 'act_applink', 'start_time', 'end_time', 'order_val', 'extras',
                  'total_member_num', 'friend_member_num', 'is_active', 'products')

class SimpleActivityEntrySerializer(serializers.ModelSerializer):
    extras = JSONParseField(read_only=True, required=False)
    class Meta:
        model = ActivityEntry
        fields = ('id', 'title', 'login_required', 'act_desc', 'act_img', 'act_logo', 'mask_link', 'act_link',
                  'act_type', 'act_applink', 'start_time', 'end_time', 'order_val',
                  'total_member_num', 'friend_member_num', 'is_active', 'extras')


class BrandEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = BrandEntry
        fields = ('id', 'brand_name', 'brand_desc', 'brand_pic', 'brand_post',
                  'brand_applink', 'start_time', 'end_time')


class BrandProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = BrandProduct
        fields = ('id', 'product_id', 'model_id', 'product_name', 'product_img', 'product_lowest_price', 'product_std_sale_price')


class BrandPortalSerializer(serializers.ModelSerializer):

    brand_products = BrandProductSerializer(many=True)
    class Meta:
        model = BrandEntry
        fields = ('id', 'brand_name', 'brand_desc', 'brand_pic', 'brand_post',
                  'brand_applink', 'brand_products', 'start_time', 'end_time')


class ProductSerializer(serializers.HyperlinkedModelSerializer):

    name = serializers.SerializerMethodField(read_only=True)
    category = ProductCategorySerializer(read_only=True)
    #     normal_skus = ProductSkuSerializer(many=True, read_only=True)
    product_model = ModelProductSerializer(source="get_product_model", read_only=True)
    is_saleout = serializers.BooleanField(source='sale_out', read_only=True)
    is_saleopen = serializers.BooleanField(source='sale_open', read_only=True)
    is_newgood = serializers.BooleanField(source='new_good', read_only=True)
    watermark_op = serializers.CharField(read_only=True)
    web_url = serializers.CharField(source='get_weburl', read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'outer_id', 'category', 'pic_path', 'remain_num', 'is_saleout', 'head_img',
                  'is_saleopen', 'is_newgood', 'std_sale_price', 'agent_price', 'sale_time', 'offshelf_time', 'memo',
                  'lowest_price', 'product_lowest_price', 'product_model', 'ware_by', 'is_verify', "model_id",
                  'watermark_op', 'web_url', 'sale_product')

    def get_name(self, obj):
        if obj.is_flatten:
            return obj.name
        return obj.name.split('/')[0]


class ProductSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        extra_kwargs = {'in_customer_shop': {}, 'shop_product_num': {}, 'rebet_amount': {},
                        'rebet_amount_des': {}, 'sale_num_des': {}}
        fields = ('id', 'pic_path', 'name', 'std_sale_price', 'agent_price', 'remain_num', 'sale_num',
                  'in_customer_shop', 'shop_product_num', 'rebet_amount', 'sale_num_des', 'rebet_amount_des')


class SimpleProductSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    category = ProductCategorySerializer(read_only=True)
    #     normal_skus = ProductSkuSerializer(many=True, read_only=True)
    product_model = SimpleModelProductSerializer(source="get_product_model", read_only=True)
    is_saleout  = serializers.SerializerMethodField(read_only=True)
    is_saleopen = serializers.BooleanField(source='sale_open', read_only=True)
    is_newgood  = serializers.BooleanField(source='new_good', read_only=True)
    watermark_op = serializers.CharField(read_only=True)
    web_url     = serializers.CharField(source='get_weburl', read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'outer_id', 'category', 'pic_path', 'head_img','std_sale_price', 'agent_price'
                  , 'sale_time', 'offshelf_time', 'lowest_price', 'product_lowest_price', 'product_model', 'model_id',
                  'is_saleout', 'is_saleopen', 'is_newgood', 'watermark_op', 'web_url')

    def get_name(self, obj):
        if obj.is_flatten:
            return obj.name
        return obj.name.split('/')[0]

    def get_is_saleout(self, obj):
        product_model = obj.product_model
        if product_model:
            return product_model.is_sale_out
        return False

class DepositProductSerializer(serializers.ModelSerializer):
    normal_skus = ProductSkuSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'outer_id', 'pic_path', 'head_img',
                  'std_sale_price', 'agent_price', 'sale_time', 'offshelf_time',
                  'product_lowest_price', 'normal_skus')


class ProductPreviewSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='rest_v1:product-detail')
    category = ProductCategorySerializer(read_only=True)
    product_model = ModelProductSerializer(read_only=True)
    is_saleout = serializers.BooleanField(source='sale_out', read_only=True)
    is_saleopen = serializers.BooleanField(source='sale_open', read_only=True)
    is_newgood = serializers.BooleanField(source='new_good', read_only=True)
    sale_charger = serializers.CharField(source="get_supplier_contactor", read_only=True)
    watermark_op = serializers.CharField(read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'url', 'name', 'outer_id', 'category', 'pic_path', 'remain_num', 'is_saleout', 'head_img',
                  'is_saleopen', 'is_newgood', 'std_sale_price', 'agent_price', 'sale_time', 'memo', 'lowest_price',
                  'product_model', 'product_lowest_price', 'ware_by', 'is_verify', "model_id", "sale_charger",
                  'watermark_op')


class PosterSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='rest_v1:goodshelf-detail')
    wem_posters = JSONParseField(read_only=True, required=False)
    chd_posters = JSONParseField(read_only=True, required=False)
    # activity = ActivityEntrySerializer(source='get_activity', read_only=True)
    # brand_promotion = BrandEntrySerializer(source='get_brands', read_only=True, many=True)

    class Meta:
        model = GoodShelf
        fields = ('id', 'url', 'wem_posters', 'chd_posters', 'active_time')


class PortalSerializer(serializers.ModelSerializer):
    """ 商城入口初始加载数据 """
    posters = JSONParseField(source='get_posters', read_only=True)
    categorys = JSONParseField(source='get_cat_imgs', read_only=True)
    activitys  = serializers.SerializerMethodField(read_only=True)
    promotion_brands   = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = GoodShelf
        fields = ('id', 'posters', 'categorys', 'activitys', 'promotion_brands' ,'active_time')

    def get_activitys(self, obj):
        now_time = datetime.datetime.now()
        activitys = ActivityEntry.get_landing_effect_activitys(now_time)
        brands_data = SimpleActivityEntrySerializer(activitys, many=True).data
        return brands_data

    def get_promotion_brands(self, obj):
        now_time = datetime.datetime.now()
        activitys = ActivityEntry.get_effect_activitys(now_time)\
            .filter(act_type=ActivityEntry.ACT_BRAND)
        brands_data = SimpleActivityEntrySerializer(activitys, many=True).data
        return brands_data

#####################################################################################

class LogisticsCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogisticsCompany
        fields = ('id', 'code', 'name')


class ShoppingCartSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='rest_v1:shoppingcart-detail')
    status = serializers.ChoiceField(choices=ShoppingCart.STATUS_CHOICE)
    item_weburl = serializers.CharField(source='get_item_weburl', read_only=True)
    class Meta:
        model = ShoppingCart
        fields = ('id', 'url', 'buyer_id', 'buyer_nick', 'item_id', 'title', 'price',
                  'std_sale_price', 'sku_id', 'num', 'total_fee', 'sku_name',
                  'pic_path', 'created', 'is_repayable', 'status', 'item_weburl')


class SaleOrderSerializer(serializers.HyperlinkedModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='rest_v1:saleorder-detail')
    status = serializers.ChoiceField(choices=SaleOrder.ORDER_STATUS)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    refund_status = serializers.ChoiceField(choices=SaleRefund.REFUND_STATUS)
    refund_status_display = serializers.CharField(source='get_refund_status_display', read_only=True)
    kill_title = serializers.BooleanField(source='second_kill_title', read_only=True)
    package_order_id = serializers.SerializerMethodField('gen_package_order_id', read_only=True)
    class Meta:
        model = SaleOrder
        fields = ('id', 'oid', 'item_id', 'title', 'sku_id', 'num', 'outer_id', 'total_fee',
                  'payment', 'discount_fee', 'sku_name', 'pic_path', 'status', 'status_display',
                  'refund_status', 'refund_status_display', "refund_id", 'kill_title',
                  'is_seckill','package_order_id')

    def gen_package_order_id(self, obj):
        if obj.package_sku:
            return obj.package_sku.package_order_id or ''
        else:
            return ''


def generate_refund_choices(obj):
    """ obj is a saletrade object """
    if not obj.status in (SaleTrade.WAIT_SELLER_SEND_GOODS,
                          SaleTrade.WAIT_BUYER_CONFIRM_GOODS,
                          SaleTrade.TRADE_BUYER_SIGNED):
        return {}

    _default = {
        obj.BUDGET: {'name': u'极速退款', 'desc_name': u'小鹿钱包',
                     'desc_tpl': u'{refund_title}，退款金额立即退到{desc_name}，并可立即支付使用，无需等待.'},
        obj.WX: {'name': u'退微信支付', 'desc_name': u'微信钱包或微信银行卡',
                 'desc_tpl': u'{refund_title}，退款金额立即退到{desc_name}，需要等待支付渠道审核３至５个工作日到账.'},
        obj.ALIPAY: {'name': u'退支付宝', 'desc_name': u'支付宝账户',
                     'desc_tpl': u'{refund_title}，退款金额立即退到{desc_name}，需要等待支付渠道审核３至５个工作日到账.'},
        'refund_title_choice': (u'申请退款后', u'退货成功后'),
    }
    is_post_refund = obj.status != SaleTrade.WAIT_SELLER_SEND_GOODS
    refund_title = _default['refund_title_choice'][is_post_refund and 1 or 0]
    refund_channels = [obj.BUDGET]
    if obj.channel != obj.BUDGET and not obj.has_budget_paid:
        refund_channels.append(obj.channel)

    refund_resp_list = []
    for channel in refund_channels:
        channel_alias = channel.split('_')[0]
        refund_param = _default.get(channel_alias)
        refund_resp_list.append({
            'refund_channel': channel,
            'name': refund_param['name'],
            'desc': refund_param['desc_tpl'].format(refund_title=refund_title,
                                                    desc_name=refund_param['desc_name'])
        })
    return {
        'refund_choices': refund_resp_list
    }

class SaleOrderDetailSerializer(serializers.HyperlinkedModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='rest_v1:saleorder-detail')
    status = serializers.ChoiceField(choices=SaleOrder.ORDER_STATUS)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    refund_status = serializers.ChoiceField(choices=SaleRefund.REFUND_STATUS)
    refund_status_display = serializers.CharField(source='get_refund_status_display', read_only=True)
    kill_title = serializers.BooleanField(source='second_kill_title', read_only=True)
    package_order_id = serializers.SerializerMethodField('gen_package_order_id', read_only=True)
    extras = serializers.SerializerMethodField('gen_extras_info', read_only=True)
    class Meta:
        model = SaleOrder
        fields = ('id', 'oid', 'item_id', 'title', 'sku_id', 'num', 'outer_id', 'total_fee',
                  'payment', 'discount_fee', 'sku_name', 'pic_path', 'status', 'status_display',
                  'refund_status', 'refund_status_display', "refund_id", 'kill_title',
                  'is_seckill', 'package_order_id', 'extras')

    def gen_package_order_id(self, obj):
        if obj.package_sku:
            return obj.package_sku.package_order_id or ''
        else:
            return ''

    def gen_extras_info(self, obj):
        return generate_refund_choices(obj.sale_trade)

class SaleTradeSerializer(serializers.HyperlinkedModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='rest_v1:saletrade-detail')
    orders = SaleOrderSerializer(source='sale_orders', many=True, read_only=True)
    # orders = serializers.HyperlinkedIdentityField(view_name='rest_v1:saletrade-saleorder')
    channel = serializers.ChoiceField(choices=SaleTrade.CHANNEL_CHOICES)
    trade_type = serializers.ChoiceField(choices=SaleTrade.TRADE_TYPE_CHOICES)
    logistics_company = LogisticsCompanySerializer(read_only=True)
    status = serializers.ChoiceField(choices=SaleTrade.TRADE_STATUS)
    status_display = serializers.CharField(source='status_name', read_only=True)
    order_pic = serializers.CharField(read_only=True)
    red_packer_num = serializers.SerializerMethodField('order_share_red_packer_num', read_only=True)

    class Meta:
        model = SaleTrade
        fields = ('id', 'orders', 'tid', 'buyer_nick', 'buyer_id', 'channel', 'payment',
                  'post_fee', 'total_fee', 'discount_fee', 'status', 'status_display', 'order_pic',
                  'buyer_message', 'trade_type', 'created', 'pay_time', 'consign_time', 'out_sid',
                  'logistics_company', 'receiver_name', 'receiver_state', 'receiver_city', 'red_packer_num',
                  'receiver_district', 'receiver_address', 'receiver_mobile', 'receiver_phone', 'order_type',
                  'can_refund')

    def order_share_red_packer_num(self, obj):
        share = OrderShareCoupon.objects.filter(uniq_id=obj.tid).first()
        if share:
            return share.remain_num
        return 0


class PackageOrderSerializer(serializers.ModelSerializer):

    pay_time = serializers.CharField(source='first_package_sku_item.pay_time', read_only=True)
    process_time = serializers.CharField(source='first_package_sku_item.process_time', read_only=True)
    book_time = serializers.CharField(source='first_package_sku_item.book_time', read_only=True)
    assign_time = serializers.CharField(source='first_package_sku_item.assign_time', read_only=True)
    finish_time = serializers.CharField(source='first_package_sku_item.finish_time', read_only=True)
    cancel_time = serializers.CharField(source='first_package_sku_item.cancel_time', read_only=True)
    ware_by_display = serializers.CharField(source='get_ware_by_display', read_only=True)
    assign_status_display = serializers.CharField(source='first_package_sku_item.get_assign_status_display', read_only=True)
    out_sid = serializers.CharField(read_only=True)
    logistics_company = LogisticsCompanySerializer(read_only=True)
    note = serializers.CharField(read_only=True)

    class Meta:
        model = PackageOrder
        fields = ('id', 'logistics_company', 'process_time', 'pay_time', 'book_time', 'assign_time',
                  'finish_time', 'cancel_time','assign_status_display', 'ware_by_display', 'out_sid', 'note')


class SaleTradeDetailSerializer(serializers.HyperlinkedModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='rest_v2:saletrade-detail')
    orders = serializers.SerializerMethodField('gen_sale_orders', read_only=True)
    # TODO 根据订单信息，显示未分包商品及已分包商品列表
    channel = serializers.ChoiceField(choices=SaleTrade.CHANNEL_CHOICES)
    trade_type = serializers.ChoiceField(choices=SaleTrade.TRADE_TYPE_CHOICES)
    logistics_company = LogisticsCompanySerializer(read_only=True)
    status = serializers.ChoiceField(choices=SaleTrade.TRADE_STATUS)
    status_display = serializers.CharField(source='status_name', read_only=True)
    package_orders = PackageOrderSerializer(many=True, read_only=True)
    package_orders = serializers.SerializerMethodField('gen_package_orders', read_only=True)
    extras = serializers.SerializerMethodField('gen_extras_info', read_only=True)
    class Meta:
        model = SaleTrade
        fields = ('id', 'orders', 'tid', 'buyer_nick', 'buyer_id', 'channel', 'payment',
                  'post_fee', 'total_fee', 'discount_fee', 'status', 'status_display',
                  'buyer_message', 'trade_type', 'created', 'pay_time', 'consign_time', 'out_sid',
                  'logistics_company', 'user_adress', 'package_orders','extras')

    def gen_sale_orders(self, obj):
        order_data_list = SaleOrderSerializer(obj.sale_orders, many=True).data
        order_data_list.sort(key=lambda x:x['package_order_id'])
        return order_data_list

    def gen_package_orders(self, obj):
        if obj.status not in SaleTrade.INGOOD_STATUS:
            return []
        package_list = PackageOrderSerializer(obj.package_orders, many=True).data
        for sale_order in obj.sale_orders.all():
            if not sale_order.is_packaged():
                package_sku_item = sale_order.package_sku
                package_list.insert(0,{
                    'id':'',
                    'logistics_company':None,
                    'process_time':package_sku_item and package_sku_item.process_time,
                    'pay_time':package_sku_item and package_sku_item.pay_time or obj.pay_time,
                    'book_time':package_sku_item and package_sku_item.book_time,
                    'assign_time':package_sku_item and package_sku_item.assign_time,
                    'finish_time':package_sku_item and package_sku_item.finish_time,
                    'cancel_time':package_sku_item and package_sku_item.cancel_time,
                    'assign_status_display':package_sku_item and package_sku_item.get_assign_status_display() or '',
                    'ware_by_display':package_sku_item and package_sku_item.get_ware_by_display() or '',
                    'out_sid':'',
                    'note':''
                })
                break
        package_list.sort(key=lambda x:x['id'])
        return package_list

    def gen_extras_info(self, obj):
        refund_dict = generate_refund_choices(obj)
        return refund_dict or {}


from flashsale.pay.models import District, UserAddress


class SaleRefundSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='rest_v1:salerefund-detail')
    good_status = serializers.ChoiceField(choices=SaleRefund.GOOD_STATUS_CHOICES)
    status = serializers.ChoiceField(choices=SaleRefund.REFUND_STATUS)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    return_address = serializers.CharField(source='get_return_address', read_only=True)
    status_shaft = JSONParseField(source='refund_status_shaft', read_only=True)
    proof_pic = JSONParseField()
    amount_flow = JSONParseField()

    class Meta:
        model = SaleRefund
        fields = ('id', 'url', 'refund_no', 'trade_id', 'order_id', 'buyer_id', 'item_id', 'title',
                  'sku_id', 'sku_name', 'refund_num', 'buyer_nick', 'mobile', 'phone', 'proof_pic',
                  'total_fee', 'payment', 'created', 'modified', 'company_name', 'sid', 'reason', 'pic_path',
                  'desc', 'feedback', 'has_good_return', 'has_good_change', 'good_status', 'status', 'refund_fee',
                  "return_address", "status_display", "amount_flow", "status_shaft", "refund_channel")


#####################################################################################

class UserAddressSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='rest_v1:useraddress-detail')
    status = serializers.ChoiceField(choices=UserAddress.STATUS_CHOICES)

    class Meta:
        model = UserAddress
        fields = ('id', 'url', 'cus_uid', 'receiver_name', 'receiver_state', 'receiver_city',
                  'receiver_district', 'receiver_address', 'receiver_zip', 'receiver_mobile',
                  'receiver_phone', 'logistic_company_code', 'default', 'status', 'created')


class DistrictSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='rest_v1:district-detail')

    class Meta:
        model = District
        fields = ('id', 'url', 'parent_id', 'name', 'grade', 'sort_order')


class UserIntegralSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Integral
        fields = ('id',
                  'integral_user',
                  'integral_value')


class UserIntegralLogSerializer(serializers.HyperlinkedModelSerializer):
    order_info = JSONParseField(source='order', read_only=True)

    class Meta:
        model = IntegralLog
        fields = ('id',
                  'integral_user',
                  'mobile',
                  'order_info',
                  'log_value',
                  'log_status',
                  'log_type',
                  'in_out',
                  'created',
                  'modified')


class TradeWuliuSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeWuliu
        exclude = ()

class ReturnWuliuSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnWuLiu
        exclude = ()

from shopapp.weixin.models import WXOrder


class WXOrderSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='rest_v1:wxorder-detail')
    order_status_display = serializers.CharField(source='get_order_status_display', read_only=True)

    class Meta:
        model = WXOrder
        fields = ('url', 'order_id', 'buyer_nick', 'order_total_price', 'order_express_price', 'order_create_time',
                  'order_status',
                  'receiver_name', 'receiver_province', 'receiver_city', 'receiver_zone', 'receiver_address',
                  'receiver_mobile',
                  'receiver_phone', 'product_id', 'product_name', 'product_price', 'product_sku', 'product_count',
                  'order_status_display', 'product_img', 'delivery_id', 'delivery_company')


##################################################################################

class CustomShareSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='rest_v1:customshare-detail')

    class Meta:
        model = CustomShare
        fields = ('url', 'id', 'title', 'desc', 'share_img', 'active_at', 'created', 'status')


from supplychain.supplier.models import SaleProduct


class SaleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleProduct


from supplychain.supplier.models import HotProduct


class HotProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotProduct


from shopback.refunds.models_refund_rate import ProRefunRcord


class ProRefunRcordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProRefunRcord
        fields = ('product', 'ref_num_out', 'ref_num_in', 'ref_sed_num', 'pro_contactor', 'pro_model', 'sale_time',
                  'pro_supplier', 'same_mod_sale_num', 'pro_pic')


class ProRefunRcdSerializer(serializers.ModelSerializer):
    """ # 针对商品的退款统计内容　
        - ProRefunRcordSerializer　fields　is to many, it makes the http request 404 return
        - To extend for client to handler the data of the pro rcd
    """

    class Meta:
        model = ProRefunRcord
        fields = ('product', 'ref_num_out', 'ref_num_in', 'ref_sed_num', 'sale_date', 'is_female', 'is_child')


from flashsale.xiaolumm.models import XiaoluMama, CarryLog, CashOut
from flashsale.clickcount.models import ClickCount, Clicks
from flashsale.clickrebeta.models import StatisticsShopping
from flashsale.xiaolumm.models.models_fortune import AwardCarry


class XiaoluMamaSerialize(serializers.ModelSerializer):
    coulde_cashout = serializers.FloatField(source='get_cash_iters', read_only=True)
    can_trial = serializers.SerializerMethodField('can_trial_judgement', read_only=True)

    class Meta:
        model = XiaoluMama
        fields = (
            "id", "get_cash_display", "charge_status", "agencylevel", "manager", "referal_from", "mobile", "weikefu",
            "charge_time", 'coulde_cashout', 'last_renew_type', 'can_trial')

    def can_trial_judgement(self, obj):
        """ 判断是否可以试用 """
        return obj.is_trialable()


class RelationShipInfoSerialize(serializers.ModelSerializer):
    nick = serializers.CharField(source='referal_to_mama_nick', read_only=True)
    thumbnail = serializers.CharField(source='referal_to_mama_img', read_only=True)
    award = serializers.SerializerMethodField('mama_award_info', read_only=True)
    charge_time = serializers.DateTimeField(source='created', read_only=True)

    class Meta:
        model = ReferalRelationship
        fields = ("id", "nick", 'thumbnail', "charge_time", "award")

    def mama_award_info(self, obj):
        return None


class PotentialInfoSerialize(serializers.ModelSerializer):
    award = serializers.SerializerMethodField('mama_award_info', read_only=True)
    charge_time = serializers.DateTimeField(source='created', read_only=True)

    class Meta:
        model = PotentialMama
        fields = ("id", "nick", 'thumbnail', "charge_time", "award")

    def mama_award_info(self, obj):
        return None


class XiaoluMamaInfoSerialize(serializers.ModelSerializer):
    nick = serializers.SerializerMethodField('mama_customer_nick', read_only=True)
    thumbnail = serializers.SerializerMethodField('mama_customer_thumbnail', read_only=True)
    award = serializers.SerializerMethodField('mama_award_info', read_only=True)

    class Meta:
        model = XiaoluMama
        fields = ("id", "agencylevel", "nick", 'thumbnail', "charge_time", "award")

    def mama_customer_nick(self, obj):
        customer = obj.get_mama_customer()
        return customer.nick if customer else ''

    def mama_customer_thumbnail(self, obj):
        customer = obj.get_mama_customer()
        return customer.thumbnail if customer else ''

    def mama_award_info(self, obj):
        referal_from_mama_id = self.context['current_mm'].id
        award_carry = AwardCarry.objects.filter(mama_id=referal_from_mama_id,
                                                contributor_mama_id=obj.id).first()
        if award_carry:
            return award_carry.carry_num / 100.0


class CarryLogSerialize(serializers.ModelSerializer):
    dayly_in_amount = serializers.FloatField(source='dayly_in_value', read_only=True)
    dayly_clk_amount = serializers.FloatField(source='dayly_clk_value', read_only=True)
    desc = serializers.CharField(source='get_carry_desc', read_only=True)

    class Meta:
        model = CarryLog
        fields = ("id", "carry_type", "xlmm", "value_money", "carry_type_name", "log_type", "carry_date", "created",
                  'dayly_in_amount', 'dayly_clk_amount', 'desc', 'get_log_type_display')


class ClickCountSerialize(serializers.ModelSerializer):
    class Meta:
        model = ClickCount
        fields = ("linkid", "agencylevel", "user_num", "valid_num", "click_num", "date")


class ClickSerialize(serializers.ModelSerializer):
    class Meta:
        model = Clicks


class StatisticsShoppingSerialize(serializers.ModelSerializer):
    pic_path = serializers.CharField(source='pro_pic', read_only=True)
    time_display = serializers.CharField(source='day_time', read_only=True)
    dayly_amount = serializers.FloatField(source='dayly_ticheng', read_only=True)

    class Meta:
        model = StatisticsShopping
        fields = ("linkid", "linkname", "wxorderid", "wxordernick", "order_cash", "rebeta_cash", "ticheng_cash",
                  "shoptime", "status", "get_status_display", "pic_path", "time_display", "dayly_amount")


class CashOutSerialize(serializers.ModelSerializer):

    class Meta:
        model = CashOut
        fields = ('id', "xlmm", "value_money", "get_status_display", "status", "get_cash_out_type_display", "created")


from flashsale.xiaolumm.models.models_advertis import XlmmAdvertis, NinePicAdver


class XlmmAdvertisSerialize(serializers.ModelSerializer):
    class Meta:
        model = XlmmAdvertis
        fields = ("title", "cntnt")


def get_mama_link(mama_id, jump_str):
    """
    获取代理专属链接
    """
    if not mama_id:
        return settings.M_SITE_URL
    if not jump_str:
        return os.path.join(settings.M_SITE_URL, "m/{0}/".format(mama_id))  # 专属链接

    preffix = 'm/{{mm_linkid}}/'
    detail_l = ''
    if (',' in jump_str and '/' not in jump_str) or str(jump_str).isdigit():  # 详情页
        model_ids = jump_str.split(',')
        model_id = random.choice(model_ids)
        c = Context({'mm_linkid': mama_id, 'model_id': model_id})
        detail_suffix = Template(''.join([preffix, '?next=mall/product/details/{{model_id}}']))  # 详情跳转页面
        detail_l = detail_suffix.render(c)
    if '/' in jump_str:
        next_suffix = Template(''.join([preffix, '?next=', jump_str]) if jump_str else '')
        c = Context({'mm_linkid': mama_id})
        detail_l = next_suffix.render(c)
    return os.path.join(settings.M_SITE_URL, detail_l)  # 专属链接


class NinePicAdverSerialize(serializers.ModelSerializer):
    pic_arry = JSONParseField()
    could_share = serializers.IntegerField(source='is_share', read_only=True)
    title = serializers.SerializerMethodField('get_description', read_only=True)  # serializers.CharField(source='description_title', read_only=True)
    description = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = NinePicAdver
        fields = ('id', "title", "start_time", 'sale_category', "turns_num", "pic_arry", 'could_share', 'description')

    def get_description(self, obj):
        """
        功能：重写描述字段
        """
        mama_id = self.context.get('request').data.get('mama_id')
        mama_link = get_mama_link(mama_id, obj.detail_modelids)
        return util_emoji.match_emoji(obj.description) + mama_link


class ModifyTimesNinePicAdverSerialize(serializers.ModelSerializer):
    class Meta:
        model = NinePicAdver
        fields = ('id',
                  'save_times',
                  'share_times')


class MamaVebViewConfSerialize(serializers.ModelSerializer):
    extra = JSONParseField()
    mama_activities = serializers.SerializerMethodField()

    class Meta:
        model = MamaVebViewConf
        fields = ('id', 'version', "is_valid", "extra", 'mama_activities', "created", "modified")

    def get_mama_activities(self, obj):
        """ 获取妈妈可以参加的活动 """
        mama_activities = ActivityEntry.mama_activities()
        serializer = ActivityEntrySerializer(mama_activities, many=True)
        return serializer.data


from flashsale.pay.models import CustomerShops, CuShopPros


class CustomerShopsSerialize(serializers.ModelSerializer):
    class Meta:
        model = CustomerShops


class CuShopProsSerialize(serializers.ModelSerializer):
    sale_num = serializers.IntegerField(source='sale_num_salt', read_only=True)

    class Meta:
        model = CuShopPros
        fields = ('id', "product", "model", "pro_status", "name", "pic_path", 'std_sale_price', 'agent_price',
                  "carry_amount", 'position', 'sale_num', 'modified', 'created', 'offshelf_time')


from flashsale.promotion.models import XLSampleSku, XLFreeSample, XLSampleOrder


class XLSampleOrderSerialize(serializers.ModelSerializer):
    class Meta:
        model = XLSampleOrder


class XLFreeSampleSerialize(serializers.ModelSerializer):
    class Meta:
        model = XLFreeSample


class XLSampleSkuSerialize(serializers.ModelSerializer):
    class Meta:
        model = XLSampleSku


from flashsale.pay.models import BudgetLog


class BudgetLogSerialize(serializers.ModelSerializer):
    budeget_detail_cash = serializers.FloatField(source='get_flow_amount_display', read_only=True)
    desc = serializers.CharField(source='log_desc', read_only=True)

    class Meta:
        model = BudgetLog
        fields = ('desc', 'budget_type', 'budget_log_type', 'budget_date', 'get_status_display', 'status', 'budeget_detail_cash', 'modified')


class XlmmFansCustomerInfoSerialize(serializers.ModelSerializer):
    """ 小鹿妈妈粉丝列表的用户信息 """

    class Meta:
        model = Customer
        fields = ('nick', 'thumbnail', 'status', 'get_status_display')


from flashsale.apprelease.models import AppRelease


class AppReleaseSerialize(serializers.ModelSerializer):
    class Meta:
        model = AppRelease


from flashsale.pay.models import FaqMainCategory, FaqsDetailCategory, SaleFaq


class SaleFaqDetailCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FaqsDetailCategory
        fields = ('id', 'main_category', 'icon_url', 'category_name', 'description')


class SaleFaqCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FaqMainCategory
        fields = ('id', 'icon_url', 'category_name', 'description')


class SaleFaqerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleFaq
        fields = ('id', 'main_category', 'detail_category', 'question', 'answer')

class FavoritesSerializer(serializers.ModelSerializer):

    modelproduct = serializers.SerializerMethodField()

    class Meta:
        model = Favorites
        fields = ('id', 'modelproduct', 'created')

    def get_modelproduct(self, obj):
        model = ModelProduct.objects.filter(id=obj.model_id).first()
        if model:
            product = model.item_product
            if product:
                web_url = product.get_weburl()
            else:
                web_url = ''
            return {
                'id': obj.model_id,
                'name': obj.name,
                'head_img': obj.head_img,
                'lowest_agent_price': obj.lowest_agent_price,
                'lowest_std_sale_price': obj.lowest_std_sale_price,
                'shelf_status': model.shelf_status,
                'web_url': web_url,
            }
        return None


class LessonTopicSerializer(serializers.ModelSerializer):
    lesson_type_display = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)

    class Meta:
        model = LessonTopic


class LessonSerializer(serializers.ModelSerializer):
    start_time_display = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    is_started = serializers.IntegerField(read_only=True)
    m_static_url = serializers.CharField(read_only=True)

    class Meta:
        extra_kwargs = {'customer_idx': {'read_only': True}}
        model = Lesson
        fields = ('id', 'lesson_topic_id', 'title', 'description', 'content_link', 'instructor_id',
                  'instructor_name', 'instructor_title', 'instructor_image', 'num_attender',
                  'num_score', 'start_time_display', 'qrcode_links', 'status', 'status_display',
                  'is_started', 'customer_idx', 'm_static_url')


class InstructorSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(read_only=True)
    apply_date = serializers.CharField(read_only=True)

    class Meta:
        model = Instructor


class LessonAttendRecordSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(read_only=True)
    signup_time = serializers.CharField(read_only=True)
    signup_date = serializers.CharField(read_only=True)

    class Meta:
        model = LessonAttendRecord
