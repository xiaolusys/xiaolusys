#-*- coding:utf8 -*-
__author__ = 'meixqhi'
import json
import time
from auth.utils import parse_datetime
from django.db import models
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
from shopback.users.models import User
from shopback.monitor.models import TradeExtraInfo
from auth import apis

LOGISTICS_FINISH_STATUS = ['ACCEPTED_BY_RECEIVER']

class Logistics(models.Model):

    tid      =  BigIntegerAutoField(primary_key=True)
    user     =  models.ForeignKey(User,null=True,related_name='logistics')

    order_code = models.CharField(max_length=64,blank=True)
    is_quick_cod_order = models.BooleanField(default=True)

    out_sid  =  models.CharField(max_length=64,blank=True)
    company_name =  models.CharField(max_length=30,blank=True)

    seller_id    =  models.CharField(max_length=64,blank=True)
    seller_nick  =  models.CharField(max_length=64,blank=True)
    buyer_nick   =  models.CharField(max_length=64,blank=True)

    item_title   = models.CharField(max_length=64,blank=True)

    delivery_start  =  models.DateTimeField(db_index=True,null=True,blank=True)
    delivery_end    =  models.DateTimeField(db_index=True,null=True,blank=True)

    receiver_name   =  models.CharField(max_length=64,blank=True)
    receiver_phone  =  models.CharField(max_length=20,blank=True)
    receiver_mobile =  models.CharField(max_length=20,blank=True)

    location        =  models.TextField(max_length=500,blank=True)
    type            =  models.CharField(max_length=7,blank=True)    #free(卖家包邮),post(平邮),express(快递),ems(EMS).

    created      =  models.DateTimeField(db_index=True,null=True,blank=True)
    modified     =  models.DateTimeField(db_index=True,null=True,blank=True)

    seller_confirm  =  models.CharField(max_length=3,default='no')
    company_name    =  models.CharField(max_length=32,blank=True)

    is_success      =  models.BooleanField(default=False)
    freight_payer   =  models.CharField(max_length=6,blank=True)
    status   =  models.CharField(max_length=32,blank=True)

    class Meta:
        db_table = 'shop_logistics_logistic'

    def __unicode__(self):
        return self.company_name
    
    @classmethod
    def get_or_create(cls,user_id,tid):
        logistic,state = cls.objects.get_or_create(tid=tid)
        if state:
            try:
                response = apis.taobao_logistics_orders_detail_get(tid=tid,tb_user_id=user_id)
                logistic_dict = response['logistics_orders_detail_get_response']['shippings']['shippings'][0]
                logistic = cls.save_logistics_through_dict(user_id, logistic_dict)
            except Exception,exc:
                logger.error('淘宝后台更新交易(tid:%s)物流信息出错'%str(trade_id),exc_info=True)
        return logistic
        
    
    @classmethod
    def save_logistics_through_dict(cls,user_id,logistic_dict):
        
        logistic,state = cls.objects.get_or_create(tid=logistic_dict['tid'])
        logistic.user = User.objects.get(visitor_id=user_id)
        for k,v in logistic_dict.iteritems():
            hasattr(logistic,k) and setattr(logistic,k,v)

        logistic.location       = json.dumps(logistic_dict.get('location',None))
        logistic.delivery_start = parse_datetime(logistic_dict['delivery_start'])\
            if logistic_dict.get('delivery_start',None) else None
        logistic.delivery_end   = parse_datetime(logistic_dict['delivery_end'])\
            if logistic_dict.get('delivery_end',None) else None
        logistic.created        = parse_datetime(logistic_dict['created'])\
            if logistic_dict.get('created',None) else None
        logistic.modified       = parse_datetime(logistic_dict['modified'])\
            if logistic_dict.get('modified',None) else None
        logistic.save()
        
        if logistic_dict['status'] in LOGISTICS_FINISH_STATUS:
            trade_extra_info,state = TradeExtraInfo.objects.get_or_create(tid=logistic_dict['tid'])
            trade_extra_info.is_update_logistic = True
            trade_extra_info.save()
        return logistic
        