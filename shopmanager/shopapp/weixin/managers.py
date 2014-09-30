#-*- coding:utf-8 -*-
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


class WeixinUserManager(models.Manager):   
    
    def get_queryset(self):
        
        super_tm = super(WeixinUserManager,self)
        #adapt to higer version django(>1.4)
        if hasattr(super_tm,'get_query_set'):
            return super_tm.get_query_set()
        return super_tm.get_queryset()
    
    
    def createReferalShip(self,referal_openid,referal_from_openid):
        
        wx_user = self.get(openid=referal_openid)
        if wx_user.referal_from_openid:
            return wx_user.referal_from_openid == referal_from_openid
        
        wx_user.referal_from_openid = referal_from_openid
        wx_user.save()
        return True
           
    
    
class VipCodeManager(models.Manager):   
    
    def get_queryset(self):
        
        super_tm = super(WeixinProductManager,self)
        #adapt to higer version django(>1.4)
        if hasattr(super_tm,'get_query_set'):
            return super_tm.get_query_set()
        return super_tm.get_queryset()
    
    
    def genVipCodeByWXUser(self,wx_user):
        
        vipcodes = self.filter(owner_openid=wx_user)
        if vipcodes.count() > 0:
            return vipcodes[0].code

        expiry = datetime.datetime(2014,9,7,0,0,0)
        code_type = 0
        code_rule = u'免费试用'
        max_usage = 10000
    
        new_code = str(random.randint(1000000,9999999))
        cnt = 0
        while True:
            cnt += 1
            try:
                vipcode = self.get(owner_openid=wx_user)
            except self.model.DoesNotExist:
                try:
                    self.create(owner_openid=wx_user,code=new_code,expiry=expiry,
                            code_type=code_type,code_rule=code_rule,max_usage=max_usage)
                except:
                    new_code = str(random.randint(1000000,9999999))
                else:
                    return new_code
            else:
                return vipcode.code
            
            if cnt > 20:
                raise Exception(u'F码生成异常')
            
            
        
    
