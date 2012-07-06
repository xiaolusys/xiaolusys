#-*- coding:utf8 -*-
__author__ = 'meixqhi'
from django.db import models


class DayMonitorStatus(models.Model):
    
    user_id = models.CharField(max_length=64)
    year  = models.IntegerField()
    month = models.IntegerField()
    day   = models.IntegerField()
    
    update_trade_increment    = models.BooleanField(default=False)
    update_purchase_increment = models.BooleanField(default=False)

    
    class Meta:
        db_table = 'shop_monitor_daymonitortatus'
        unique_together = ("user_id","year","month","day")
    


class TradeExtraInfo(models.Model):

    tid   =  models.BigIntegerField(primary_key=True)

    is_update_amount = models.BooleanField(default=False)
    is_update_logistic = models.BooleanField(default=False)
    is_picking_print = models.BooleanField(default=False)
    is_send_sms      = models.BooleanField(default=False)

    modified         = models.DateTimeField(auto_now=True)
    seller_memo      = models.TextField(max_length=128,blank=True)

    class Meta:
        db_table = 'shop_monitor_tradeextrainfo'
        



  