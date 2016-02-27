# coding=utf-8
from shopback.items.models import Product,ProductSku,ProductCategory
from flashsale.pay.models import (
    SaleTrade,
    SaleOrder,
    SaleRefund,
    LogisticsCompany,
    Productdetail,
    ModelProduct,
    ShoppingCart,
    Customer,
    Register,
    GoodShelf,
    ActivityEntry,
    CustomShare,
    UserBudget
)
from shopback.trades.models import TradeWuliu
from flashsale.xiaolumm.models import XiaoluMama
from rest_framework import serializers


class RegisterSerializer(serializers.HyperlinkedModelSerializer):


    class Meta:
        model = Register
        fields = ('id','vmobile')

class XiaoluMamaSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model  = XiaoluMama
        fields = ('id','cash','agencylevel','created','status')


class UserBudgetSerialize(serializers.HyperlinkedModelSerializer):
    budget_cash = serializers.FloatField(source='get_amount_display', read_only=True)
    is_cash_out = serializers.IntegerField(source='is_could_cashout', read_only=True)

    class Meta:
        model = UserBudget
        fields = ('budget_cash', 'is_cash_out')

class CustomerSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(view_name='v1:customer-detail')
    user_id  = serializers.CharField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    xiaolumm = XiaoluMamaSerializer(source='getXiaolumm', read_only=True)
    user_budget = UserBudgetSerialize(source='getBudget', read_only=True)
    has_usable_password = serializers.BooleanField(source='user.has_usable_password', read_only=True)
    is_attention_public = serializers.IntegerField(source='is_attention_wx_public', read_only=True)

    class Meta:
        model = Customer
        fields = ('id', 'url', 'user_id', 'username', 'nick', 'mobile', 'email','phone',
                  'thumbnail','status', 'created', 'modified', 'xiaolumm', 'has_usable_password',
                  'user_budget', 'is_attention_public')


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

class JsonListField(serializers.Field):

    def to_representation(self, obj):
        return [s.strip() for s in obj.split() if s.startswith(('http://','https://'))]

    def to_internal_value(self, data):
        return data

class ProductdetailSerializer(serializers.ModelSerializer):

    head_imgs = JsonListField(read_only=True,required=False)
    content_imgs = JsonListField(read_only=True,required=False)

    class Meta:
        model = Productdetail
        fields = ( 'head_imgs', 'content_imgs', 'mama_discount', 'is_recommend',
                   'buy_limit', 'per_limit', 'mama_rebeta', 'material', 'wash_instructions', 'note', 'color')

class ModelProductSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(read_only=True)
    head_imgs = JsonListField(read_only=True,required=False)
    content_imgs = JsonListField(read_only=True,required=False)
    is_single_spec = serializers.BooleanField(read_only=True)
    is_sale_out = serializers.BooleanField(read_only=True)

    class Meta:
        model = ModelProduct
        fields = ( 'id','name','head_imgs', 'content_imgs', 'is_single_spec', 'is_sale_out', 'buy_limit', 'per_limit')
        
        
class ActivityEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = ActivityEntry
        fields = ( 'id','title', 'login_required', 'act_desc', 'act_img', 'mask_link', 'act_link', 'act_applink',
                   'start_time', 'end_time')

class ProductSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(view_name='v1:product-detail')
    category = ProductCategorySerializer(read_only=True)
#     normal_skus = ProductSkuSerializer(many=True, read_only=True)
    product_model = ModelProductSerializer(source="get_product_model",read_only=True)
    is_saleout    = serializers.BooleanField(source='sale_out', read_only=True)
    is_saleopen   = serializers.BooleanField(source='sale_open',read_only=True)
    is_newgood    = serializers.BooleanField(source='new_good',read_only=True)
    watermark_op = serializers.CharField(read_only=True)

    class Meta:
        model = Product
        fields = ('id','url', 'name', 'outer_id', 'category', 'pic_path','remain_num', 'is_saleout','head_img',
                  'is_saleopen', 'is_newgood','std_sale_price', 'agent_price', 'sale_time', 'offshelf_time', 'memo',
                  'lowest_price', 'product_lowest_price', 'product_model', 'ware_by', 'is_verify', "model_id", 'watermark_op')


class ProductPreviewSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(view_name='v1:product-detail')
    category = ProductCategorySerializer(read_only=True)
    product_model = ModelProductSerializer(read_only=True)
    is_saleout    = serializers.BooleanField(source='sale_out', read_only=True)
    is_saleopen   = serializers.BooleanField(source='sale_open',read_only=True)
    is_newgood    = serializers.BooleanField(source='new_good',read_only=True)
    sale_charger = serializers.CharField(source="get_supplier_contactor", read_only=True)
    watermark_op = serializers.CharField(read_only=True)
    
    class Meta:
        model = Product
        fields = ('id','url', 'name', 'outer_id', 'category', 'pic_path','remain_num', 'is_saleout','head_img',
                  'is_saleopen', 'is_newgood','std_sale_price', 'agent_price', 'sale_time', 'memo', 'lowest_price',
                   'product_model','product_lowest_price','ware_by','is_verify',"model_id", "sale_charger",'watermark_op')


class JSONParseField(serializers.Field):
    def to_representation(self, obj):
        return obj

    def to_internal_value(self, data):
        return data


class PosterSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(view_name='v1:goodshelf-detail')
    wem_posters = JSONParseField(read_only=True,required=False)
    chd_posters = JSONParseField(read_only=True,required=False)
    activity    = ActivityEntrySerializer(source='get_activity',read_only=True)
    
    class Meta:
        model = GoodShelf
        fields = ('id','url','wem_posters','chd_posters','active_time','activity')

#####################################################################################

class LogisticsCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogisticsCompany
        fields = ('id', 'code', 'name')


class ShoppingCartSerializer(serializers.HyperlinkedModelSerializer):

    url     = serializers.HyperlinkedIdentityField(view_name='v1:shoppingcart-detail')
    status      = serializers.ChoiceField(choices=ShoppingCart.STATUS_CHOICE)

    class Meta:
        model = ShoppingCart
        fields = ( 'id', 'url','buyer_id', 'buyer_nick', 'item_id', 'title', 'price', 'std_sale_price',
                    'sku_id', 'num', 'total_fee', 'sku_name', 'pic_path', 'created', 'status')


class SaleOrderSerializer(serializers.HyperlinkedModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='v1:saleorder-detail')
    status = serializers.ChoiceField(choices=SaleOrder.ORDER_STATUS)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    refund_status = serializers.ChoiceField(choices=SaleRefund.REFUND_STATUS)
    refund_status_display = serializers.CharField(source='get_refund_status_display', read_only=True)
    kill_title = serializers.BooleanField(source='second_kill_title', read_only=True)

    class Meta:
        model = SaleOrder
        fields = ('id', 'oid', 'item_id', 'title', 'sku_id', 'num', 'outer_id', 'total_fee',
                  'payment', 'discount_fee', 'sku_name', 'pic_path', 'status', 'status_display',
                  'refund_status', 'refund_status_display', "refund_id", 'kill_title')


class SaleTradeSerializer(serializers.HyperlinkedModelSerializer):

    url     = serializers.HyperlinkedIdentityField(view_name='v1:saletrade-detail')
    orders  = SaleOrderSerializer(source='sale_orders',many=True,read_only=True)
    #orders = serializers.HyperlinkedIdentityField(view_name='v1:saletrade-saleorder')
    channel    = serializers.ChoiceField(choices=SaleTrade.CHANNEL_CHOICES)
    trade_type = serializers.ChoiceField(choices=SaleTrade.TRADE_TYPE_CHOICES)
    logistics_company = LogisticsCompanySerializer(read_only=True)
    status     = serializers.ChoiceField(choices=SaleTrade.TRADE_STATUS)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    order_pic  = serializers.CharField(read_only=True)

    class Meta:
        model = SaleTrade
        fields = ( 'id', 'url', 'orders', 'tid', 'buyer_nick', 'buyer_id', 'channel', 'payment',
                    'post_fee', 'total_fee', 'discount_fee', 'status','status_display','order_pic',
                    'buyer_message', 'trade_type', 'created', 'pay_time', 'consign_time', 'out_sid',
                   'logistics_company', 'receiver_name', 'receiver_state', 'receiver_city',
                   'receiver_district', 'receiver_address','receiver_mobile', 'receiver_phone')


from flashsale.pay.models import District,UserAddress


class SaleRefundSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:salerefund-detail')
    good_status = serializers.ChoiceField(choices=SaleRefund.GOOD_STATUS_CHOICES)
    status = serializers.ChoiceField(choices=SaleRefund.REFUND_STATUS)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    proof_pic = JSONParseField()

    class Meta:
        model = SaleRefund
        fields = ('id', 'url', 'refund_no', 'trade_id', 'order_id', 'buyer_id', 'item_id', 'title',
                  'sku_id', 'sku_name', 'refund_num', 'buyer_nick', 'mobile', 'phone', 'proof_pic',
                  'total_fee', 'payment', 'created', 'modified', 'company_name', 'sid', 'reason', 'pic_path',
                  'desc', 'feedback', 'has_good_return', 'has_good_change', 'good_status', 'status', 'refund_fee',
                  "status_display")


#####################################################################################

class UserAddressSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(view_name='v1:useraddress-detail')
    status      = serializers.ChoiceField(choices=UserAddress.STATUS_CHOICES)

    class Meta:
        model = UserAddress
        fields = ( 'id', 'url', 'cus_uid', 'receiver_name', 'receiver_state', 'receiver_city',
                   'receiver_district', 'receiver_address', 'receiver_zip', 'receiver_mobile',
                    'receiver_phone', 'default', 'status', 'created')


class DistrictSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(view_name='v1:district-detail')
    class Meta:
        model = District
        fields = ( 'id' , 'url', 'parent_id', 'name', 'grade', 'sort_order')


from flashsale.pay.models_coupon import IntegralLog, Integral, CouponPool, Coupon


class UserIntegralSerializer(serializers.HyperlinkedModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='v1:user-intergral')

    class Meta:
        model = Integral
        fields = ('id', 'integral_user', 'integral_value')

class UserIntegralLogSerializer(serializers.HyperlinkedModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='v1:user-IntegralLog')

    class Meta:
        model = IntegralLog
        fields = ('id', 'integral_user', 'mobile', 'order_info', 'log_value', 'log_status', 'log_type', 'in_out', 'created','modified')


class UserCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ('id', 'coupon_user', 'coupon_no', 'mobile', 'trade_id', 'created', 'modified', 'status')


class UserCouponPoolSerializer(serializers.ModelSerializer):
    coupon_title = serializers.CharField(source='get_coupon_type_display', read_only=True)
    class Meta:
        model = CouponPool
        fields = ('id', 'deadline', 'coupon_value', 'coupon_type','coupon_status','coupon_title')



class TradeWuliuSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeWuliu
        exclude=()

from flashsale.pay.models_coupon_new import UserCoupon, CouponTemplate


class UsersCouponSerializer(serializers.ModelSerializer):
    coupon_type = serializers.IntegerField(source='cp_id.template.type', read_only=True)
    coupon_type_display = serializers.CharField(source='cp_id.template.get_type_display', read_only=True)
    deadline = serializers.CharField(source='cp_id.template.deadline', read_only=True)
    title = serializers.CharField(source='cp_id.template.title', read_only=True)
    coupon_no = serializers.CharField(source='cp_id.coupon_no', read_only=True)
    poll_status = serializers.IntegerField(source='cp_id.status', read_only=True)
    coupon_value = serializers.FloatField(source='cp_id.template.value', read_only=True)
    valid = serializers.BooleanField(source='cp_id.template.valid', read_only=True)
    use_fee = serializers.FloatField(source='cp_id.template.use_fee', read_only=True)

    class Meta:
        model = UserCoupon
        # remove the "cp_id" field, test for browser solwly
        fields = ("id",  "coupon_type", 'title', "customer", 'coupon_no', 'coupon_value', 'valid',
                  'poll_status', "deadline", "sale_trade", "status", "created", "modified", 'use_fee',
                  'coupon_type_display')


class CouponTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponTemplate


from shopapp.weixin.models import WXOrder


class WXOrderSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(view_name='v1:wxorder-detail')
    order_status_display  = serializers.CharField(source='get_order_status_display', read_only=True)

    class Meta:
        model = WXOrder
        fields = ( 'url','order_id', 'buyer_nick', 'order_total_price', 'order_express_price', 'order_create_time', 'order_status',
                    'receiver_name', 'receiver_province', 'receiver_city', 'receiver_zone','receiver_address','receiver_mobile',
                    'receiver_phone', 'product_id', 'product_name', 'product_price', 'product_sku', 'product_count',
                    'order_status_display', 'product_img', 'delivery_id', 'delivery_company')


##################################################################################

class CustomShareSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(view_name='v1:customshare-detail')

    class Meta:
        model = CustomShare
        fields = ('url','id','title', 'desc', 'share_img', 'active_at', 'created', 'status')


from supplychain.supplier.models import SaleProduct


class SaleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleProduct


from supplychain.supplier.models_hots import HotProduct


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


class XiaoluMamaSerialize(serializers.ModelSerializer):
    coulde_cashout = serializers.FloatField(source='get_cash_iters', read_only=True)
    class Meta:
        model = XiaoluMama
        fields = ("id", "get_cash_display", "charge_status", "agencylevel", "manager", "referal_from", "mobile", "weikefu",
                  "charge_time", 'coulde_cashout')


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
        fields = ('id', "xlmm", "value_money", "get_status_display", "status", "created")


from flashsale.xiaolumm.models_advertis import XlmmAdvertis, NinePicAdver


class XlmmAdvertisSerialize(serializers.ModelSerializer):
    class Meta:
        model = XlmmAdvertis
        fields = ("title", "cntnt")


class NinePicAdverSerialize(serializers.ModelSerializer):
    pic_arry = JSONParseField()
    could_share = serializers.IntegerField(source='is_share', read_only=True)
    title = serializers.CharField(source='description_title', read_only=True)

    class Meta:
        model = NinePicAdver
        fields = ('id', "title", "start_time", "turns_num", "pic_arry", 'could_share', 'description')


from flashsale.pay.models_shops import CustomerShops, CuShopPros


class CustomerShopsSerialize(serializers.ModelSerializer):
    class Meta:
        model = CustomerShops


class CuShopProsSerialize(serializers.ModelSerializer):
    class Meta:
        model = CuShopPros


from flashsale.promotion.models import XLSampleSku, XLSampleApply, XLFreeSample, XLSampleOrder, XLInviteCode


class XLSampleOrderSerialize(serializers.ModelSerializer):
    class Meta:
        model = XLSampleOrder


class XLFreeSampleSerialize(serializers.ModelSerializer):
    class Meta:
        model = XLFreeSample


class XLSampleSkuSerialize(serializers.ModelSerializer):
    class Meta:
        model = XLSampleSku

from flashsale.pay.models_user import BudgetLog


class BudgetLogSerialize(serializers.ModelSerializer):
    budeget_detail_cash = serializers.FloatField(source='get_flow_amount_display', read_only=True)
    desc = serializers.CharField(source='log_desc', read_only=True)

    class Meta:
        model = BudgetLog
        fields = ('desc', 'budget_type', 'budget_log_type', 'budget_date', 'status', 'budeget_detail_cash')


class XlmmFansCustomerInfoSerialize(serializers.ModelSerializer):
    """ 小鹿妈妈粉丝列表的用户信息 """

    class Meta:
        model = Customer
        fields = ('nick', 'thumbnail', 'status', 'get_status_display')

