from rest_framework import serializers
from .models import Product, ProductSku, Item, DepositeDistrict
from shopback.users.models import User
# class CategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Category
#         fields = ('cid', 'parent_cid', 'name', 'status', 'sort_order')

class ProductSerializer(serializers.ModelSerializer):
     
    class Meta:
    
        model = Product
        # fields =  ('cid','parent_cid' ,'is_parent' ,'name','status','sort_order')
#         fields = ('parent_cid' ,'is_parent' ) 
        exclude = ('created',)
 
class  ProductSkuSerializer(serializers.ModelSerializer):
     
    class Meta:
    
        model = ProductSku
        # fields =  ('cid','parent_cid' ,'is_parent' ,'name','status','sort_order')
#         fields = ('parent_cid' ,'is_parent' ) 
        exclude = ('created',)       
        
class ProductItemSerializer(serializers.ModelSerializer):
    """ docstring for ProductItem ModelResource """
    class Meta:
        model = Item
    # fields = ('id','outer_id','name','outer_sku_id','properties_name','price','num') 
        exclude = ('desc',)        
    
    
    
class DepositeDistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositeDistrict
        fields = ("district_no", "parent_no", "location", "in_use", "extra_info")
         
         
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # fields=("district_no","parent_no","location","in_use","extra_inf")
        exclude = ('created_at',)
    
    
class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        # fields=("district_no","parent_no","location","in_use","extra_inf")
        exclude = ('desc',)
        
