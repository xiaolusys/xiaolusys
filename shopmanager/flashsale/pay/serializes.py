from django.forms import model_to_dict
from rest_framework import serializers

from shopback.items.models import Product,ProductSku


class ProductSerializer(serializers.ModelSerializer):
    
#     category = SaleCategorySerializer()
    class Meta:
        model = Product
        fields = ('id','name','category','pic_path','collect_num','std_sale_price',
                  'agent_price','status','created','memo')
        
    
class ProductSkuField(serializers.Field):
    def to_representation(self, obj):
        
        sku_list  = []
        for sku in obj.all():
            sku_list.append(model_to_dict(sku))
        return sku_list

    def to_internal_value(self, data):
        return data


        
class ProductDetailSerializer(serializers.ModelSerializer):
    
#     category = SaleCategorySerializer()
    prod_skus = ProductSkuField()
    class Meta:
        model = Product
        fields = ('id','name','category','pic_path','collect_num','std_sale_price',
                  'agent_price','status','created','memo','prod_skus')