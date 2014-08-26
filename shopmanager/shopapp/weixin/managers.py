#-*- coding:utf8 -*-
import random
import datetime
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
        
        from .weixin_apis import WeiXinAPI

        _wx_api = WeiXinAPI()
        product_dict = _wx_api.getMerchant(product_id)
        
        return self.createByDict(product_dict)
        
    
    def createByDict(self,product_dict):
        
        product_id = product_dict['product_id']
        
        product,state = self.get_or_create(product_id=product_id)
        
        for k,v in product_dict.iteritems():
            hasattr(product,k) and setattr(product,k,v)
            
        product.product_name = product.product_base.get('name','')
        product.product_img  = product.product_base.get('img','')
         
        product.save()
        
        return product
    
    @property
    def UPSHELF(self):
        return self.get_query_set().filter(status=self.model.UP_SHELF)
    
    @property
    def DOWNSHELF(self):
        return self.get_query_set().filter(status=self.model.DOWN_SHELF)
            
    
class VipCodeManager(models.Manager):   
    
    def get_queryset(self):
        
        super_tm = super(WeixinProductManager,self)
        #adapt to higer version django(>1.4)
        if hasattr(super_tm,'get_query_set'):
            return super_tm.get_query_set()
        return super_tm.get_queryset()
    
    
    def genVipCodeByWXUser(self,wx_user):
        
        vip_code,state = self.get_or_create(owner_openid=wx_user)
        if vip_code.code :
            return vip_code.code
        
        expiry = datetime.datetime(2014,8,11,0,0,0)
        code_type = 0
        code_rule = u'免费试用'
        max_usage = 10000
    
        new_code = str(random.randint(1000000,9999999))
        cnt = 0
        while True:
            cnt += 1
            objs = self.filter(code=new_code)
            if objs.count() < 0 or cnt > 20:
                break
            new_code = str(random.randint(1000000,9999999))
            
        vip_code.code=new_code 
        vip_code.expiry=expiry
        vip_code.code_type=code_type
        vip_code.code_rule=code_rule
        vip_code.max_usage=max_usage
        vip_code.save()
        
        return new_code
    
    
