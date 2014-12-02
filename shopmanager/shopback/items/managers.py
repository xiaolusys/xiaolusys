#-*- coding:utf8 -*-
from django.db import models
from shopback import paramconfig as pcfg
from common.utils import update_model_fields


class ProductManager(models.Manager):
    
    def getProductByOuterid(self,outer_id):
        
        try:
            return self.get(outer_id=outer_id)
        except Product.DoesNotExist:
            None
    
    def getProductByBarcode(self,barcode):
        
        if not barcode or not isinstance(barcode,(str,unicode)) or len(barcode)==0:
            return []
        
        from shopback.items.models import ProductSku
        
        product_skus = ProductSku.objects.filter(product__status__in=(pcfg.NORMAL,pcfg.REMAIN),barcode=barcode)
        if product_skus.count() > 0:
            return list(set([sku.product for sku in product_skus]))
        
        products = self.filter(status__in=(pcfg.NORMAL,pcfg.REMAIN),barcode=barcode)
        if products.count() > 0:
            return [ p for p in products]
        
        bar_len = len(barcode)
        for index in range(0,bar_len-1):
            products = self.filter(outer_id=barcode[0:bar_len-index])
            if products.count() > 0:
                return [ p for p in products]
            
        return []
    
    def getBarcodeByOuterid(self,outer_id,outer_sku_id=''):
        
        product = self.get(outer_id=outer_id)
        product_sku = None
        if outer_sku_id:
            product_sku = product.prod_skus.get(outer_id=outer_sku_id)
            
        return product_sku and product_sku.BARCODE or product.BARCODE
            
    
    def getProductSkuByOuterid(self,outer_id,outer_sku_id):
        
        from .models import ProductSku
        try:
            return ProductSku.objects.get(outer_id=outer_sku_id,
                                          product__outer_id=outer_id)
        except ProductSku.DoesNotExist:
            None
            
    def isProductOutOfStock(self,outer_id,outer_sku_id):
        
        from .models import Product,ProductSku
        try:
            product = self.get(outer_id=outer_id)
            product_sku = None
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)
        except (self.model.DoesNotExist,ProductSku.DoesNotExist):
            raise self.model.ProductCodeDefect(u'(%s,%s)编码组合未匹配到商品'%(outer_id,outer_sku_id))
        
        return (product.is_out_stock,
                product_sku and product_sku.is_out_stock)[product_sku and 1 or 0]
    
    def isProductRuelMatch(self,outer_id,outer_sku_id):
        
        from .models import Product,ProductSku
        try:
            product = self.get(outer_id=outer_id)
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)
                return product_sku.is_match
            
            return product.is_match
        except (self.model.DoesNotExist,ProductSku.DoesNotExist):
            raise self.model.ProductCodeDefect(u'(%s,%s)编码组合未匹配到商品'%(outer_id,outer_sku_id))
        
    def isProductRuleSplit(self,outer_id,outer_sku_id):
        
        from .models import Product,ProductSku
        try:
            product = self.get(outer_id=outer_id)
            product_sku = None
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)
                return product_sku.is_split
            return product.is_split
            
        except (self.model.DoesNotExist,ProductSku.DoesNotExist):
            raise self.model.ProductCodeDefect(u'(%s,%s)编码组合未匹配到商品'%(outer_id,outer_sku_id))
        
    
    def getProductMatchReason(self,outer_id,outer_sku_id):
        
        from .models import Product,ProductSku
        try:
            product = self.get(outer_id=outer_id)
            
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)
                return (product_sku.match_reason 
                        or product.match_reason 
                        or u'匹配原因不明')
            
            return product.match_reason or u'匹配原因不明'
   
        except (self.model.DoesNotExist,ProductSku.DoesNotExist):
            raise self.model.ProductCodeDefect(u'(%s,%s)编码组合未匹配到商品'%(outer_id,outer_sku_id))
        
        
    def getPrudocutCostByCode(self,outer_id,outer_sku_id):
        
        from .models import ProductSku
        try:
            product = self.get(outer_id=outer_id)
            product_sku = None
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)
        except (self.model.DoesNotExist,ProductSku.DoesNotExist):
            raise self.model.ProductCodeDefect(u'(%s,%s)编码组合未匹配到商品'%(outer_id,outer_sku_id))
        
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
                
        except (self.model.DoesNotExist,ProductSku.DoesNotExist):
            raise self.model.ProductCodeDefect(u'(%s,%s)编码组合未匹配到商品'%(outer_id,outer_sku_id))
        
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
                
        except (self.model.DoesNotExist,ProductSku.DoesNotExist):
            raise self.model.ProductCodeDefect(u'(%s,%s)编码组合未匹配到商品'%(outer_id,outer_sku_id))
        
    def trancecode(self,outer_id,outer_sku_id,sku_code_prior=False):
        
        conncate_code = outer_sku_id or outer_id
        
        index  = conncate_code.rfind(self.model.PRODUCT_CODE_DELIMITER)
        if sku_code_prior and index > 0:
            return conncate_code[index+1:],conncate_code[0:index]
        
        if index > 0:
            return conncate_code[0:index],conncate_code[index+1:]
            
        return outer_id,outer_sku_id
    
    
    
    
    
