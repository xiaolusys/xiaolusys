from django.db import models
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey

ORDER_SUCCESS_STATUS = ['WAIT_SELLER_SEND_GOODS','WAIT_BUYER_CONFIRM_GOODS','TRADE_BUYER_SIGNED','TRADE_FINISHED']
ORDER_FINISH_STATUS  = 'TRADE_FINISHED'
ORDER_UNPAY_STATUS   = 'WAIT_BUYER_PAY'

class Trade(models.Model):

    id           =  BigIntegerAutoField(primary_key=True)

    seller_id    =  models.CharField(max_length=32,blank=True)
    seller_nick  =  models.CharField(max_length=64,blank=True)
    buyer_nick   =  models.CharField(max_length=64,blank=True)
    type         =  models.CharField(max_length=32,blank=True)

    year  = models.IntegerField(null=True,db_index=True)
    month = models.IntegerField(null=True,db_index=True)
    week  = models.IntegerField(null=True,db_index=True)
    day   = models.IntegerField(null=True,db_index=True)
    hour  = models.CharField(max_length=5,blank=True,db_index=True)

    created      =  models.DateTimeField(null=True,blank=True)
    payment      =  models.CharField(max_length=10,blank=True)
    discount_fee =  models.CharField(max_length=10,blank=True)
    adjust_fee   =  models.CharField(max_length=10,blank=True)
    post_fee    =  models.CharField(max_length=10,blank=True)
    total_fee   =  models.CharField(max_length=10,blank=True)

    commission_fee =  models.CharField(max_length=10,blank=True)

    pay_time    =  models.DateTimeField(null=True,blank=True)
    end_time    =  models.DateTimeField(null=True,blank=True)
    modified    =  models.DateTimeField(null=True,blank=True)

    buyer_message    =  models.CharField(max_length=256,blank=True)
    buyer_memo       =  models.CharField(max_length=128,blank=True)
    seller_memo      =  models.CharField(max_length=128,blank=True)

    status      =  models.CharField(max_length=30,blank=True)


    class Meta:
        db_table = 'shop_trade'




    def save_trade_through_dict(self,user_id,t):

        import time
        from auth.utils import parse_datetime

        self.id = t['tid']
        self.seller_id = user_id
        for k,v in t.iteritems():
            hasattr(self,k) and setattr(self,k,v)

        dt = parse_datetime(t['created'])
        self.year  = dt.year
        self.hour  = dt.hour
        self.month = dt.month
        self.day   = dt.day
        self.week  = time.gmtime(time.mktime(dt.timetuple()))[7]/7+1

        self.created  = parse_datetime(t['created'])
        self.pay_time = parse_datetime(t['pay_time']) if t.get('pay_time',None) else None
        self.end_time = parse_datetime(t['end_time']) if t.get('end_time',None) else None
        self.modified = parse_datetime(t['modified']) if t.get('modified',None) else None

        self.save()





class Order(models.Model):

    oid   = BigIntegerAutoField(primary_key=True)

    trade = BigIntegerForeignKey(Trade,related_name='trade_orders')
    title =  models.CharField(max_length=128)
    price = models.CharField(max_length=12,blank=True)
    num_iid = models.BigIntegerField(null=True)

    item_meal_id = models.IntegerField(null=True)
    sku_id = models.CharField(max_length=20,blank=True)
    num = models.IntegerField(null=True)

    outer_sku_id = models.CharField(max_length=20,blank=True)
    total_fee = models.CharField(max_length=12,blank=True)

    payment = models.CharField(max_length=12,blank=True)
    discount_fee = models.CharField(max_length=12,blank=True)
    adjust_fee = models.CharField(max_length=12,blank=True)

    modified = models.CharField(max_length=19,blank=True)
    sku_properties_name = models.CharField(max_length=88,blank=True)
    refund_id = models.BigIntegerField(null=True)

    is_oversold = models.BooleanField()
    is_service_order = models.BooleanField()

    item_meal_name = models.CharField(max_length=88,blank=True)
    pic_path = models.CharField(max_length=128,blank=True)

    seller_nick = models.CharField(max_length=32,blank=True,db_index=True)
    buyer_nick = models.CharField(max_length=32,blank=True)

    refund_status = models.CharField(max_length=40,blank=True)

    outer_iid = models.CharField(max_length=64,blank=True)

    cid = models.BigIntegerField(null=True)
    status = models.CharField(max_length=30,blank=True)

    class Meta:
        db_table = 'shop_order'




