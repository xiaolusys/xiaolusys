#encoding:utf8
__author__ = 'meixqhi'
import json
import time
from auth.utils import parse_datetime
from django.db import models
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
from shopback.users.models import User
import logging

logger = logging.getLogger('exception.handler')


class PurchaseOrder(models.Model):

    fenxiao_id = models.CharField(max_length=64,primary_key=True)
    id         = models.CharField(max_length=64,blank=True)

    user       = models.ForeignKey(User,null=True,related_name='purchases')

    seller_id          = models.CharField(max_length=64,blank=True)
    supplier_username  = models.CharField(max_length=64,blank=True)
    supplier_memo      = models.TextField(max_length=1000,blank=True)
    supplier_from      = models.CharField(max_length=20,blank=True)

    distributor_from   = models.CharField(max_length=20,blank=True)
    distributor_username    = models.CharField(max_length=32,blank=True)
    distributor_payment     = models.CharField(max_length=10,blank=True)

    logistics_id       = models.CharField(db_index=True,max_length=64,blank=True)
    logistics_company_name  = models.CharField(max_length=64,blank=True)
    consign_time       = models.DateTimeField(db_index=True,null=True,blank=True)

    pay_time   = models.DateTimeField(db_index=True,null=True,blank=True)
    pay_type   = models.CharField(max_length=32,blank=True)

    post_fee   = models.CharField(max_length=10,blank=True)
    total_fee  = models.CharField(max_length=10,blank=True)

    shipping   = models.CharField(max_length=10,blank=True)
    trade_type = models.CharField(max_length=10,blank=True)
    memo       = models.TextField(max_length=1000,blank=True)

    created    = models.DateTimeField(null=True,blank=True)
    modified   = models.DateTimeField(null=True,blank=True)

    sub_purchase_orders = models.TextField(max_length=5000,blank=True)

    tc_order_id = models.CharField(max_length=64,blank=True)
    alipay_no   = models.CharField(max_length=64,blank=True)
    status     = models.CharField(max_length=32,blank=True)

    class Meta:
        db_table = 'shop_purchaseorder'

    def __unicode__(self):
        return str(self.fenxiao_id)

    @property
    def sub_purchase_orders_dict(self):
        return json.loads(self.sub_purchase_orders) if self.sub_purchase_orders else None


    def save_order_through_dict(self,seller_id,order):

        self.user  =  User.objects.get(visitor_id=seller_id)
        for k,v in order.iteritems():
            hasattr(self,k) and setattr(self,k,v)

        self.created  = parse_datetime(order['created']) if order.get('created',None) else None
        self.pay_time = parse_datetime(order['pay_time']) if order.get('pay_time',None) else None
        self.modified = parse_datetime(order['modified']) if order.get('modified',None) else None
        self.consign_time = parse_datetime(order['consign_time']) if order.get('consign_time',None) else None

        self.sub_purchase_orders = json.dumps(order['sub_purchase_orders'])
        self.save()

  