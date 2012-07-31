#-*- coding:utf8 -*-
__author__ = 'meixqhi'
import json
import time
from auth.utils import parse_datetime
from django.db import models
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
from shopback.users.models import User



REFUND_WILL_STATUS    = ['WAIT_BUYER_RETURN_GOODS','WAIT_SELLER_CONFIRM_GOODS','SUCCESS']
REFUND_STATUS = (
    ('WAIT_SELLER_AGREE','买家已经申请退款，等待卖家同意'),
    ('WAIT_BUYER_RETURN_GOODS','卖家已经同意退款，等待买家退货'),
    ('WAIT_SELLER_CONFIRM_GOODS','买家已经退货，等待卖家确认收货'),
    ('SELLER_REFUSE_BUYER','卖家拒绝退款'),
    ('CLOSED','退款关闭'),
    ('SUCCESS','退款成功'),
)


class Refund(models.Model):

    refund_id    = BigIntegerAutoField(primary_key=True)
    tid          = models.BigIntegerField(null=True)

    title        = models.CharField(max_length=64,blank=True)
    num_iid      = models.BigIntegerField(null=True)

    user         = models.ForeignKey(User,null=True,related_name='refunds')
    seller_id    = models.CharField(max_length=64,blank=True)
    buyer_nick   = models.CharField(max_length=64,blank=True)
    seller_nick  = models.CharField(max_length=64,blank=True)

    total_fee    = models.CharField(max_length=10,blank=True)
    refund_fee   = models.CharField(max_length=10,blank=True)
    payment      = models.CharField(max_length=10,blank=True)

    created   = models.DateTimeField(db_index=True,null=True,blank=True)
    modified  = models.DateTimeField(db_index=True,null=True,blank=True)

    oid       = models.CharField(db_index=True,max_length=64,blank=True)
    company_name = models.CharField(max_length=64,blank=True)
    sid       = models.CharField(max_length=64,blank=True)

    reason    = models.TextField(max_length=200,blank=True)
    desc      = models.TextField(max_length=1000,blank=True)
    has_good_return = models.BooleanField(default=False)

    good_status  = models.CharField(max_length=32,blank=True)
    order_status = models.CharField(max_length=32,blank=True)
    status       = models.CharField(max_length=32,blank=True)

    class Meta:
        db_table = 'shop_refunds_refund'

    def __unicode__(self):
        return str(self.refund_id)

    def save_refund_through_dict(self,seller_id,refund):

        self.user  = User.objects.get(visitor_id=seller_id)
        for k,v in refund.iteritems():
            hasattr(self,k) and setattr(self,k,v)

        self.created  = parse_datetime(refund['created']) \
            if refund.get('created',None) else None
        self.modified = parse_datetime(refund['modified']) \
            if refund.get('modified',None) else None

        self.save()
        
