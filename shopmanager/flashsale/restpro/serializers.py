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
    GoodShelf
    )
from rest_framework import serializers


class RegisterSerializer(serializers.HyperlinkedModelSerializer):
    
    
    class Meta:
        model = Register
        fields = ('id','vmobile')
        

class CustomerSerializer(serializers.HyperlinkedModelSerializer):
    
    url = serializers.HyperlinkedIdentityField(view_name='v1:customer-detail')
    user_id = serializers.CharField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Customer
        fields = ('id', 'url', 'user_id', 'username', 'nick', 'mobile', 'email','phone', 
                  'status', 'created', 'modified')


#####################################################################################
class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ('cid', 'parent_cid', 'name', 'status', 'sort_order')

class ProductSkuSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSku
        fields = ('id', 'outer_id', 'name', 'remain_num', 'std_sale_price', 'agent_price')

class JsonListField(serializers.Field):
    
    def to_representation(self, obj):
        return [s.strip() for s in obj.split('\n') if s.startswith(('http://','https://'))]
        
    def to_internal_value(self, data):
        return data

class ProductdetailSerializer(serializers.ModelSerializer):
    
    head_imgs = JsonListField()
    content_imgs = JsonListField()
    
    class Meta:
        model = Productdetail
        fields = ( 'head_imgs', 'content_imgs', 'mama_discount', 'is_recommend', 'buy_limit','per_limit','mama_rebeta')

class ModelProductSerializer(serializers.ModelSerializer):
    
    head_imgs = JsonListField()
    content_imgs = JsonListField()
    
    class Meta:
        model = ModelProduct
        fields = ( 'name','head_imgs', 'content_imgs', 'mama_discount', 'is_recommend', 'buy_limit','per_limit')

class ProductSerializer(serializers.HyperlinkedModelSerializer):
    
    url = serializers.HyperlinkedIdentityField(view_name='v1:product-detail')
    category = ProductCategorySerializer(read_only=True)
#     normal_skus = ProductSkuSerializer(many=True, read_only=True)
    product_model = ModelProductSerializer()
    
    class Meta:
        model = Product
        fields = ('id','url', 'name', 'outer_id', 'category', 'pic_path','remain_num', 
                  'std_sale_price', 'agent_price', 'sale_time', 'memo', 'product_model')

import json

class JSONParseField(serializers.Field):
    def to_representation(self, obj):
        return obj
    
    def to_internal_value(self, data):
        return data


class PosterSerializer(serializers.HyperlinkedModelSerializer):
    
    url = serializers.HyperlinkedIdentityField(view_name='v1:goodshelf-detail')
    wem_posters = JSONParseField()
    chd_posters = JSONParseField()
    
    class Meta:
        model = GoodShelf
        fields = ('id','url','wem_posters','chd_posters','active_time')

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
        fields = ( 'id', 'url','buyer_id', 'buyer_nick', 'item_id', 'title', 'price', 'sku_id',
                   'num', 'total_fee', 'sku_name', 'pic_path', 'created', 'status')


class SaleOrderSerializer(serializers.HyperlinkedModelSerializer):
    
#     url        = serializers.HyperlinkedIdentityField(view_name='v1:saleorder-detail')
    status     = serializers.ChoiceField(choices=SaleOrder.ORDER_STATUS)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    refund_status  = serializers.ChoiceField(choices=SaleRefund.REFUND_STATUS)
    refund_status_display = serializers.CharField(source='get_refund_status_display', read_only=True)
    
    class Meta:
        model = SaleOrder
        fields = ( 'id', 'oid', 'item_id', 'title', 'sku_id' , 'num', 'outer_id', 
                   'total_fee' , 'payment', 'sku_name', 'pic_path', 'status' ,'status_display',
                   'refund_status', 'refund_status_display')
        

class SaleTradeSerializer(serializers.HyperlinkedModelSerializer):
    
    url = serializers.HyperlinkedIdentityField(view_name='v1:saletrade-detail')
    orders = serializers.HyperlinkedIdentityField(view_name='v1:saletrade-saleorder')
    channel    = serializers.ChoiceField(choices=SaleTrade.CHANNEL_CHOICES)
    trade_type = serializers.ChoiceField(choices=SaleTrade.TRADE_TYPE_CHOICES)
    logistics_company = LogisticsCompanySerializer(read_only=True)
    status     = serializers.ChoiceField(choices=SaleTrade.TRADE_STATUS)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    order_pic = serializers.CharField(read_only=True)
    
    class Meta:
        model = SaleTrade
        fields = ( 'id', 'url', 'orders', 'tid', 'buyer_nick', 'buyer_id', 'channel', 'payment', 'post_fee', 'total_fee', 'discount_fee', 'status',
                   'status_display','order_pic','buyer_message', 'trade_type', 'created', 'pay_time', 'consign_time', 'out_sid', 'logistics_company',
                   'receiver_name', 'receiver_state', 'receiver_city', 'receiver_district', 'receiver_mobile', 'receiver_phone')
        
 
from flashsale.pay.models import SaleRefund,District,UserAddress
       

class SaleRefundSerializer(serializers.HyperlinkedModelSerializer):
    
    url = serializers.HyperlinkedIdentityField(view_name='v1:salerefund-detail')
    good_status = serializers.ChoiceField(choices=SaleRefund.GOOD_STATUS_CHOICES)
    status      = serializers.ChoiceField(choices=SaleRefund.REFUND_STATUS)
    
    class Meta:
        model = SaleRefund
        fields = ( 'id', 'url', 'refund_no', 'trade_id', 'order_id', 'buyer_id', 'item_id', 'title',
                   'sku_id', 'sku_name', 'refund_num','buyer_nick', 'mobile', 'phone',
                    'total_fee', 'payment', 'created', 'company_name', 'sid', 'reason',
                   'desc','feedback','has_good_return','has_good_change', 'good_status', 'status')
        

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
        
                        
