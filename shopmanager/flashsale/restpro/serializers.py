from shopback.items.models import Product,ProductSku,ProductCategory
from flashsale.pay.models import SaleTrade,LogisticsCompany,Productdetail,ShoppingCart
from rest_framework import serializers

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ('cid', 'parent_cid', 'name', 'status', 'sort_order')

class ProductSkuSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSku
        fields = ('id', 'outer_id', 'name', 'remain_num', 'std_sale_price', 'agent_price')


class ProductSerializer(serializers.HyperlinkedModelSerializer):
    
    category = ProductCategorySerializer(read_only=True)
    normal_skus = ProductSkuSerializer(many=True, read_only=True)
#     details =  serializers.HyperlinkedIdentityField(view_name='product-detail')
    
    class Meta:
        model = Product
        fields = ('id', 'name', 'outer_id', 'category', 'pic_path','remain_num', 
                  'std_sale_price', 'agent_price', 'sale_time', 'memo', 'normal_skus')


class LogisticsCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogisticsCompany
        fields = ('id', 'code', 'name')


class ShoppingCartSerializer(serializers.HyperlinkedModelSerializer):
    
    status      = serializers.ChoiceField(choices=ShoppingCart.STATUS_CHOICE)
    
    class Meta:
        model = ShoppingCart
        fields = ( 'id', 'buyer_id', 'buyer_nick', 'item_id', 'title', 'price', 'sku_id',
                   'num', 'total_fee', 'sku_name', 'pic_path', 'created', 'status')
        

class SaleTradeSerializer(serializers.HyperlinkedModelSerializer):
    
    channel = serializers.ChoiceField(choices=SaleTrade.CHANNEL_CHOICES)
    trade_type = serializers.ChoiceField(choices=SaleTrade.TRADE_TYPE_CHOICES)
    logistics_company = LogisticsCompanySerializer(read_only=True)
    
    class Meta:
        model = SaleTrade
        fields = ( 'id', 'tid', 'buyer_nick', 'buyer_id', 'channel', 'payment', 'post_fee', 'total_fee',
                   'buyer_message', 'trade_type', 'created', 'pay_time', 'consign_time', 'out_sid', 'logistics_company',
                   'receiver_name', 'receiver_state', 'receiver_city', 'receiver_district', 'receiver_mobile', 'receiver_phone')
        
 
from flashsale.pay.models import SaleRefund,District,UserAddress
       

class SaleRefundSerializer(serializers.HyperlinkedModelSerializer):
    
    good_status = serializers.ChoiceField(choices=SaleRefund.GOOD_STATUS_CHOICES)
    status      = serializers.ChoiceField(choices=SaleRefund.REFUND_STATUS)
    
    class Meta:
        model = SaleRefund
        fields = ( 'id', 'refund_no', 'trade_id', 'order_id', 'buyer_id', 'item_id', 'title',
                   'sku_id', 'sku_name', 'refund_num','buyer_nick', 'mobile', 'phone',
                    'total_fee', 'payment', 'created', 'company_name', 'sid', 'reason',
                   'desc','feedback','has_good_return','has_good_change', 'good_status', 'status')
        
        
class UserAddressSerializer(serializers.HyperlinkedModelSerializer):
    
    status      = serializers.ChoiceField(choices=UserAddress.STATUS_CHOICES)
    
    class Meta:
        model = UserAddress
        fields = ( 'id', 'cus_uid', 'receiver_name', 'receiver_state', 'receiver_city', 
                   'receiver_district', 'receiver_address', 'receiver_zip', 'receiver_mobile',
                    'receiver_phone', 'default', 'status', 'created')
        

class DistrictSerializer(serializers.HyperlinkedModelSerializer):
    
    class Meta:
        model = District
        fields = ( 'id', 'parent_id', 'name', 'grade', 'sort_order')
        
                        
