#encoding:utf8
__author__ = 'meixqhi'
import json
import time
from auth.utils import parse_datetime
from django.db import models
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
from shopback.users.models import User



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
        db_table = 'shop_logistic'

    def __unicode__(self):
        return self.company_name

    def save_logistics_through_dict(self,user_id,t):

        self.user = User.objects.get(visitor_id=user_id)
        for k,v in t.iteritems():
            hasattr(self,k) and setattr(self,k,v)

        self.location       = json.dumps(t.get('location',None))
        self.delivery_start = parse_datetime(t['delivery_start']) if t.get('delivery_start',None) else None
        self.delivery_end   = parse_datetime(t['delivery_end']) if t.get('delivery_end',None) else None
        self.created        = parse_datetime(t['created']) if t.get('created',None) else None
        self.modified       = parse_datetime(t['modified']) if t.get('modified',None) else None
        self.save()