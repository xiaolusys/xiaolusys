import json
import time
from auth.utils import parse_datetime
from django.db import models
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey

ORDER_SUCCESS_STATUS  = ['WAIT_SELLER_SEND_GOODS','WAIT_BUYER_CONFIRM_GOODS','TRADE_BUYER_SIGNED','TRADE_FINISHED']
ORDER_UNFINISH_STATUS = ['WAIT_SELLER_SEND_GOODS','WAIT_BUYER_CONFIRM_GOODS','TRADE_BUYER_SIGNED']
ORDER_FINISH_STATUS   = 'TRADE_FINISHED'
ORDER_UNPAY_STATUS    = 'WAIT_BUYER_PAY'
REFUND_WILL_STATUS    = ['WAIT_BUYER_RETURN_GOODS','WAIT_SELLER_CONFIRM_GOODS','SUCCESS']

class Trade(models.Model):

    id           =  BigIntegerAutoField(primary_key=True)

    seller_id    =  models.CharField(max_length=32,blank=True,db_index=True)
    seller_nick  =  models.CharField(max_length=64,blank=True)
    buyer_nick   =  models.CharField(max_length=64,blank=True)
    type         =  models.CharField(max_length=32,blank=True)

    year  = models.IntegerField(null=True,db_index=True)
    month = models.IntegerField(null=True,db_index=True)
    week  = models.IntegerField(null=True,db_index=True)
    day   = models.IntegerField(null=True,db_index=True)
    hour  = models.CharField(max_length=5,blank=True,db_index=True)

    payment      =  models.CharField(max_length=10,blank=True)
    discount_fee =  models.CharField(max_length=10,blank=True)
    adjust_fee   =  models.CharField(max_length=10,blank=True)
    post_fee    =  models.CharField(max_length=10,blank=True)
    total_fee   =  models.CharField(max_length=10,blank=True)

    buyer_obtain_point_fee  =  models.CharField(max_length=10,blank=True)
    point_fee        =  models.CharField(max_length=10,blank=True)
    real_point_fee   =  models.CharField(max_length=10,blank=True)
    commission_fee   =  models.CharField(max_length=10,blank=True)

    created       =  models.DateTimeField(db_index=True,null=True,blank=True)
    pay_time      =  models.DateTimeField(null=True,blank=True)
    end_time      =  models.DateTimeField(db_index=True,null=True,blank=True)
    modified      =  models.DateTimeField(db_index=True,null=True,blank=True)
    consign_time  =  models.DateTimeField(db_index=True,null=True,blank=True)

    buyer_message    =  models.CharField(max_length=1000,blank=True)
    buyer_memo       =  models.CharField(max_length=1000,blank=True)
    seller_memo      =  models.CharField(max_length=1000,blank=True)

    shipping_type    =  models.CharField(max_length=12,blank=True)
    buyer_alipay_no  =  models.CharField(max_length=128,blank=True)
    receiver_name    =  models.CharField(max_length=64,blank=True)
    receiver_state   =  models.CharField(max_length=8,blank=True)
    receiver_city    =  models.CharField(max_length=8,blank=True)
    receiver_district  =  models.CharField(max_length=16,blank=True)

    receiver_address   =  models.CharField(max_length=64,blank=True)
    receiver_zip       =  models.CharField(max_length=10,blank=True)
    receiver_mobile    =  models.CharField(max_length=20,blank=True)
    receiver_phone     =  models.CharField(max_length=20,blank=True)

    status      =  models.CharField(max_length=32,blank=True)

    class Meta:
        db_table = 'shop_trade'

    def __unicode__(self):
        return str(self.id)

    @classmethod
    def save_trade_through_dict(cls,user_id,trade_dict):

        trade,state = Trade.objects.get_or_create(pk=trade_dict['tid'])
        trade.seller_id = user_id
        for k,v in trade_dict.iteritems():
            hasattr(trade,k) and setattr(trade,k,v)

        dt = parse_datetime(trade_dict['created'])
        trade.year  = dt.year
        trade.hour  = dt.hour
        trade.month = dt.month
        trade.day   = dt.day
        trade.week  = time.gmtime(time.mktime(dt.timetuple()))[7]/7+1

        trade.created  = parse_datetime(trade_dict['created'])
        trade.pay_time = parse_datetime(trade_dict['pay_time']) \
                           if trade_dict.get('pay_time',None) else None
        trade.end_time = parse_datetime(trade_dict['end_time']) \
                           if trade_dict.get('end_time',None) else None
        trade.modified = parse_datetime(trade_dict['modified']) \
                           if trade_dict.get('modified',None) else None
        trade.consign_time = parse_datetime(trade_dict['consign_time']) \
                           if trade_dict.get('consign_time',None) else None
        trade.save()

        order = Order()
        order.seller_nick = trade_dict['seller_nick']
        order.buyer_nick  = trade_dict['buyer_nick']
        order.trade       = trade

        for o in trade_dict['orders']['order']:
            for k,v in o.iteritems():
                hasattr(order,k) and setattr(order,k,v)
            order.save()

        return trade



class TradeExtraInfo(models.Model):

    tid   =  models.BigIntegerField(primary_key=True)

    is_update_amount = models.BooleanField(default=False)
    is_picking_print = models.BooleanField(default=False)
    is_send_sms      = models.BooleanField(default=False)

    modified         = models.DateTimeField(auto_now=True)
    seller_memo      = models.TextField(max_length=128,blank=True)

    class Meta:
        db_table = 'shop_tradeextrainfo'



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
    sku_properties_name = models.CharField(max_length=256,blank=True)
    refund_id = models.BigIntegerField(null=True)

    is_oversold = models.BooleanField()
    is_service_order = models.BooleanField()

    item_meal_name = models.CharField(max_length=88,blank=True)
    pic_path = models.CharField(max_length=128,blank=True)

    seller_nick = models.CharField(max_length=32,blank=True,db_index=True)
    buyer_nick  = models.CharField(max_length=32,blank=True)

    refund_status = models.CharField(max_length=40,blank=True)
    outer_id = models.CharField(max_length=64,blank=True)

    cid    = models.BigIntegerField(null=True)
    status = models.CharField(max_length=32,blank=True)

    class Meta:
        db_table = 'shop_order'

    def __unicode__(self):
        return str(self.oid)



class Logistics(models.Model):

    tid      =  BigIntegerAutoField(primary_key=True)
    out_sid  =  models.CharField(max_length=64,blank=True)
    company_name =  models.CharField(max_length=30,blank=True)

    seller_id    =  models.CharField(max_length=32,blank=True)
    seller_nick  =  models.CharField(max_length=64,blank=True)
    buyer_nick   =  models.CharField(max_length=64,blank=True)

    delivery_start  =  models.DateTimeField(db_index=True,null=True,blank=True)
    delivery_end    =  models.DateTimeField(db_index=True,null=True,blank=True)

    item_title      =  models.CharField(max_length=64,blank=True)
    receiver_name   =  models.CharField(max_length=64,blank=True)
    created      =  models.DateTimeField(db_index=True,null=True,blank=True)
    modified     =  models.DateTimeField(db_index=True,null=True,blank=True)

    type         =  models.CharField(max_length=10,blank=True)
    freight_payer   =  models.CharField(max_length=6,blank=True)
    seller_confirm  =  models.CharField(max_length=3,default='no')
    status   =  models.CharField(max_length=32,blank=True)

    class Meta:
        db_table = 'shop_logistic'

    def __unicode__(self):
        return str(self.tid)

    def save_logistics_through_dict(self,user_id,t):

        self.seller_id = user_id
        for k,v in t.iteritems():
            hasattr(self,k) and setattr(self,k,v)

        self.delivery_start = parse_datetime(t['delivery_start']) if t.get('delivery_start',None) else None
        self.delivery_end   = parse_datetime(t['delivery_end']) if t.get('delivery_end',None) else None
        self.created        = parse_datetime(t['created']) if t.get('created',None) else None
        self.modified       = parse_datetime(t['modified']) if t.get('modified',None) else None
        self.save()





class PurchaseOrder(models.Model):

    fenxiao_id = models.CharField(max_length=64,primary_key=True)
    id         = models.CharField(max_length=64,blank=True)

    seller_id  = models.CharField(max_length=64,db_index=True,blank=True)

    supplier_username  = models.CharField(max_length=64,blank=True)
    supplier_memo      = models.CharField(max_length=256,blank=True)
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
    memo       = models.CharField(max_length=256,blank=True)

    created    = models.DateTimeField(null=True,blank=True)
    modified   = models.DateTimeField(null=True,blank=True)

    sub_purchase_orders = models.CharField(max_length=5000,blank=True)

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

        self.seller_id = seller_id
        for k,v in order.iteritems():
            hasattr(self,k) and setattr(self,k,v)

        self.created  = parse_datetime(order['created']) if order.get('created',None) else None
        self.pay_time = parse_datetime(order['pay_time']) if order.get('pay_time',None) else None
        self.modified = parse_datetime(order['modified']) if order.get('modified',None) else None
        self.consign_time = parse_datetime(order['consign_time']) if order.get('consign_time',None) else None

        self.sub_purchase_orders = json.dumps(order['sub_purchase_orders'])

        self.save()





class Refund(models.Model):

    refund_id    = BigIntegerAutoField(primary_key=True)
    trade        = BigIntegerForeignKey(Trade,null=True,blank=True,related_name='refunds')
    title        = models.CharField(max_length=64,blank=True)

    seller_id    = models.CharField(max_length=64,db_index=True,blank=True)
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

    reason    = models.CharField(max_length=200,blank=True)
    desc      = models.CharField(max_length=500,blank=True)
    has_good_return = models.BooleanField(default=False)

    good_status  = models.CharField(max_length=32,blank=True)
    order_status = models.CharField(max_length=32,blank=True)
    status       = models.CharField(max_length=32,blank=True)

    class Meta:
        db_table = 'shop_refund'

    def __unicode__(self):
        return str(self.refund_id)

    def save_refund_through_dict(self,seller_id,refund):

        self.seller_id = seller_id
        try:
            trade = Trade.objects.get(pk=refund['tid'])
        except Trade.DoesNotExist:
            import logging
            logger = logging.getLogger('trade.refund')
            logger.error('Trade(id:%s) is not exist.'%refund['tid'])
            trade = None

        self.trade = trade
        for k,v in refund.iteritems():
            hasattr(self,k) and setattr(self,k,v)

        self.created  = parse_datetime(refund['created']) \
            if refund.get('created',None) else None
        self.modified = parse_datetime(refund['modified']) \
            if refund.get('modified',None) else None

        self.save()



class MonthTradeReportStatus(models.Model):

    seller_id   = models.CharField(max_length=64,blank=True)

    year  = models.IntegerField(null=True)
    month = models.IntegerField(null=True)

    update_order    = models.BooleanField(default=False)
    update_purchase = models.BooleanField(default=False)
    update_amount   = models.BooleanField(default=False)
    update_logistics  = models.BooleanField(default=False)
    update_refund   = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=Trade)

    class Meta:
        db_table = 'shop_monthreportstatus'
        unique_together = ("seller_id","year","month")



#class TradeSerialId(models.Model):
#
#    year  = models.IntegerField()
#    month = models.IntegerField()
#    day   = models.IntegerField()
#
#    serial_no = models.IntegerField(default=1)
#
#    class Meta:
#        db_table = 'shop_tradeserialid'
#        unique_together = ("year","month","day")