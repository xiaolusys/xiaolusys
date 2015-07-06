from shopback.items.models import Product,ProductSku,ProductCategory
from flashsale.pay.models import SaleTrade,LogisticsCompany,Productdetail
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
        fields = ('pk', 'id', 'name', 'outer_id', 'category', 'pic_path','remain_num', 
                  'std_sale_price', 'agent_price', 'sale_time', 'memo', 'normal_skus')


class LogisticsCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogisticsCompany
        fields = ('id', 'code', 'name')
        

class SaleTradeSerializer(serializers.HyperlinkedModelSerializer):
    
    channel = serializers.ChoiceField(choices=SaleTrade.CHANNEL_CHOICES)
    trade_type = serializers.ChoiceField(choices=SaleTrade.TRADE_TYPE_CHOICES)
    logistics_company = LogisticsCompanySerializer(read_only=True)
    
    class Meta:
        model = SaleTrade
        fields = ('id', 'tid', 'buyer_nick', 'buyer_id', 'channel', 'payment', 'post_fee', 'total_fee',
                   'buyer_message', 'trade_type', 'created', 'pay_time', 'consign_time', 'out_sid', 'logistics_company',
                   'receiver_name', 'receiver_state', 'receiver_city', 'receiver_district', 'receiver_mobile', 'receiver_phone')
        
        
        
