#-*- coding:utf8 -*-
from django.db import models
from django.db.models import Q,Sum
from django.db.models.signals import post_save
from django.db import IntegrityError, transaction

class WeixinProductManager(models.Manager):
    
    def get_queryset(self):
        
        super_tm = super(WeixinProductManager,self)
        #adapt to higer version django(>1.4)
        if hasattr(super_tm,'get_query_set'):
            return super_tm.get_query_set()
        return super_tm.get_queryset()
    
    def getOrCreate(self,product_id):
        
        product,state = self.get_or_create(product_id=product_id)
        
        if not state and product.status:
            return product
        
        _wx_api = WeiXinAPI()
        product_dict = _wx_api.getMerchant(product_id)
        
        return self.createByDict(product_dict)
        
    
    def createByDict(self,product_dict):
        
        product_id = product_dict['product_id']
        
        product,state = self.get_or_create(product_id=product_id)
        
        for k,v in product_dict.iteritems():
            hasattr(product,k) and setattr(product,k,v)
            
        product.product_name = product.product_base.name
        product.product_img  = product.product_base.img
         
        product.save()
        
        return product
    
    @property
    def UPSHELF(self):
        return self.get_query_set().filter(status=self.model.UP_SHELF)
    
    @property
    def DOWNSHELF(self):
        return self.get_query_set().filter(status=self.model.DOWN_SHELF)
            
    
    