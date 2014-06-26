#-*- coding:utf8 -*-
from django.db import models
from common.utils import update_model_fields

class ProductDefectException(Exception):
    pass

class ProductManager(models.Manager):
    
    def getProductByOuterid(self,outer_id):
        
        try:
            return self.get(outer_id=outer_id)
        except Product.DoesNotExist:
            None
        
    def getProductSkuByOuterid(self,outer_id,outer_sku_id):
        
        from .models import ProductSku
        try:
            return ProductSku.objects.get(outer_id=outer_sku_id,
                                          product__outer_id=outer_id)
        except ProductSku.DoesNotExist:
            None
            
    def isProductOutOfStock(self,outer_id,outer_sku_id):
        
        from .models import ProductSku
        try:
            product = self.get(outer_id=outer_id)
            product_sku = None
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)
        except (Product.DoesNotExist,ProductSku.DoesNotExsit):
            raise ProductDefectException(u'(%s,%s)编码组合未匹配到商品')
        
        return (product.is_out_stock,
                product_sku and product_sku.is_out_stock)[product_sku and 1 or 0]
    
    def isProductRuelMatch(self,outer_id,outer_sku_id):
        
        from .models import ProductSku
        try:
            product = self.get(outer_id=outer_id)
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)
                return product_sku.is_match
            
            return product.is_match
        except (Product.DoesNotExist,ProductSku.DoesNotExsit):
            raise ProductDefectException(u'(%s,%s)编码组合未匹配到商品')
        
    
    def getProductMatchReason(self,outer_id,outer_sku_id):
        
        from .models import ProductSku
        try:
            product = self.get(outer_id=outer_id)
            
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)
                return (product_sku.match_reason 
                        or product.match_reason 
                        or u'匹配原因不明')
            
            return product.match_reason or u'匹配原因不明'
   
        except (Product.DoesNotExist,ProductSku.DoesNotExsit):
            raise ProductDefectException(u'(%s,%s)编码组合未匹配到商品')
        
        
    def getPrudocutCostByCode(self,outer_id,outer_sku_id):
        
        from .models import ProductSku
        try:
            product = self.get(outer_id=outer_id)
            product_sku = None
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)
        except (Product.DoesNotExist,ProductSku.DoesNotExsit):
            raise ProductDefectException(u'(%s,%s)编码组合未匹配到商品')
        
        return (product.cost,
                product_sku and product_sku.cost)[product_sku and 1 or 0]
    
    
    def updateWaitPostNumByCode(self,outer_id,outer_sku_id,order_num):
        
        from .models import ProductSku
        try:
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)
                product_sku.update_wait_post_num(order_num)
                
            else:
                product = self.get(outer_id=outer_id)
                product.update_wait_post_num(order_num)
                
        except (Product.DoesNotExist,ProductSku.DoesNotExsit):
            raise ProductDefectException(u'(%s,%s)编码组合未匹配到商品')
        
    def reduceWaitPostNumByCode(self,outer_id,outer_sku_id,order_num):
        
        from .models import ProductSku
        try:
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)
                product_sku.update_wait_post_num(order_num,dec_update=True)
                
            else:
                product = self.get(outer_id=outer_id)
                product.update_wait_post_num(order_num,dec_update=True)
                
        except (Product.DoesNotExist,ProductSku.DoesNotExsit):
            raise ProductDefectException(u'(%s,%s)编码组合未匹配到商品')
        
    def trancecode(self,outer_id,outer_sku_id):
        
        if outer_sku_id :
            index  = outer_sku_id.rfind(self.model.PRODUCT_CODE_DELIMITER)
            if index > 0:
                return outer_sku_id[0:index],outer_sku_id[index:]
        
        return outer_id,outer_sku_id
    
    