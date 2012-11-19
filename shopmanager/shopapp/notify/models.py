#-*- coding:utf8 -*-
from django.db import models
from shopback.base.fields import BigIntegerAutoField
from auth.utils import parse_datetime


class ItemNotify(models.Model):
    id      = BigIntegerAutoField(primary_key=True)
    user_id = models.BigIntegerField()
    num_iid = models.BigIntegerField()
    
    title   = models.CharField(max_length=64,blank=True)
    
    sku_id  = models.BigIntegerField(null=True,blank=True)
    sku_num = models.IntegerField(null=True,default=0)
    status  = models.CharField(max_length=32,blank=True)
    
    increment = models.IntegerField(null=True,default=0)
    nick    = models.CharField(max_length=32,blank=True)
    num     = models.IntegerField(null=True,default=0)
    
    changed_fields = models.CharField(max_length=256,blank=True)
    price   = models.CharField(max_length=10,blank=True)
    modified = models.DateTimeField(db_index=True,null=True,blank=True) 
       
    is_exec  = models.BooleanField(default=False)
    class Meta:
        db_table = 'shop_notify_item'
        unique_together = ("user_id","num_iid","sku_id","status")
        
    def __unicode__(self):
        return '<%d,%d,%s,%s>'%(self.user_id,self.num_iid,str(self.sku_id),self.status)
    
    
class TradeNotify(models.Model):
    id      = BigIntegerAutoField(primary_key=True)
    user_id = models.BigIntegerField()
    tid     = models.BigIntegerField()
    oid     = models.BigIntegerField()
    
    nick    = models.CharField(max_length=64,blank=True)
    
    seller_nick = models.CharField(max_length=64,blank=True)
    buyer_nick  = models.CharField(max_length=64,blank=True)
    
    payment   = models.CharField(max_length=10,blank=True)
    type      = models.CharField(max_length=32,blank=True)
    
    status  = models.CharField(max_length=32,blank=True)
    
    trade_mark = models.CharField(max_length=256,blank=True)
   
    modified = models.DateTimeField(db_index=True,null=True,blank=True)
    
    is_exec  = models.BooleanField(default=False)
    class Meta:
        db_table = 'shop_notify_trade'
        unique_together = ("user_id","tid","oid","status")
        
    def __unicode__(self):
        return '<%d,%d,%d,%s>'%(self.user_id,self.tid,self.oid,self.status)
    
    
class RefundNotify(models.Model):
    id      = BigIntegerAutoField(primary_key=True)
    user_id = models.BigIntegerField()
    tid     = models.BigIntegerField()
    oid     = models.BigIntegerField()
    rid     = models.BigIntegerField()
    
    nick    = models.CharField(max_length=64,blank=True)
    seller_nick  = models.CharField(max_length=64,blank=True)
    buyer_nick   = models.CharField(max_length=64,blank=True)
    
    refund_fee   = models.CharField(max_length=10,blank=True)
    status  = models.CharField(max_length=32,blank=True)
    
    modified = models.DateTimeField(db_index=True,null=True,blank=True)
    
    is_exec  = models.BooleanField(default=False)
    class Meta:
        db_table = 'shop_notify_refund'
        unique_together = ("user_id","tid","oid","rid","status")
        
    def __unicode__(self):
        return '<%d,%d,%d,%d,%s>'%(self.user_id,self.tid,self.oid,self.rid,self.status)
   
    
