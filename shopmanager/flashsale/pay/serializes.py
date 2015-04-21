from django.forms import model_to_dict
from rest_framework import serializers

from shopback.items.models import Product,ProductSku
from .models import District,UserAddress
        
class DetailInfoField(serializers.Field):
    
    def to_representation(self, obj):
        
        detail_dict  = {'head_imgs':[],'content_imgs':[]}
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
        print 'internal value',data
        return data
    

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
    
#    category = SaleCategorySerializer()
    details   = DetailInfoField()
    prod_skus = ProductSkuField()
    class Meta:
        model = Product
        fields = ('id','name','category','pic_path','collect_num','std_sale_price',
                  'agent_price','status','created','memo','prod_skus','details')
        

class UserAddressSerializer(serializers.ModelSerializer):
    
#    category = SaleCategorySerializer()
    class Meta:
        model = UserAddress
        fields = ('id','cus_uid','receiver_name','receiver_state','receiver_city','receiver_district',
                  'receiver_address','receiver_zip','receiver_mobile','receiver_phone','default')




    