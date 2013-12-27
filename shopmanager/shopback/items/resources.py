#-*- coding:utf8 -*-
__author__ = 'meixqhi'
from djangorestframework.resources import ModelResource
from shopback.items.models import Product,ProductSku,Item
from shopback.items.serializer import ProductSerializer,ItemSerializer

class ProductListResource(ModelResource):
    """ docstring for ProductList ModelResource """

    model = Product
    fields = ('id','outer_id','name','category','wait_post_num','collect_num','warn_num','remain_num','price','modified','sync_stock'
               ,'is_stock_warn','is_warning','is_assign','is_split','is_match','post_check','status','match_reason','buyer_prompt','memo') 
    exclude = ('url',)
    
    
class ProductResource(ModelResource):
    """ docstring for Product ModelResource """

    model = Product
    fields = ('id','outer_id','outer_sku_id','name','category','collect_num','warn_num','cost','modified',
                'remain_num','wait_post_num','weight','std_purchase_price','std_sale_price','agent_price','staff_price',
               'sync_stock','is_split','is_match','is_assign','is_stock_warn','post_check','is_warning',
               'skus','sku','status','match_reason','buyer_prompt','memo','barcode','warn_skus','assign_template') 
    exclude = ('url',)
    
    
class ProductItemResource(ModelResource):
    """ docstring for ProductItem ModelResource """

    model = Item
    fields = ('id','outer_id','name','outer_sku_id','properties_name','price','num') 
    exclude = ('url',)
    
    
class ProductSkuResource(ModelResource):
    """ docstring for ProductSku ModelResource """

    model = ProductSku
    fields = ('outer_id','product','wait_post_num','quantity','warn_num','remain_num','properties_name','properties_alias','is_stock_warn'
              ,'cost','std_sale_price','agent_price','staff_price','is_warning','sync_stock','is_assign','is_split','is_match','status','layer_table') 
    exclude = ('url',)
    
    
class ProductDistrictResource(ModelResource):
    """ docstring for ProductSku ModelResource """

    model = Product
    fields = ('product',) 
    exclude = ('url',)