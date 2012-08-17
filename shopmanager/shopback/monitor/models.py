#-*- coding:utf8 -*-
__author__ = 'meixqhi'
from django.db import models

class SystemConfig(models.Model):
    
    is_rule_auto = models.BooleanField(default=False)   #是否开启自动规则过滤
    is_sms_auto  = models.BooleanField(default=False)   #是否开启自动短信提醒
    
    is_flag_auto = models.BooleanField(default=False)
    is_confirm_delivery_auto = models.BooleanField(default=False) #是否自动确认发货
    
    class Meta:
        db_table = 'shop_monitor_systemconfig'
    
    @classmethod
    def getconfig(cls):
        configs = cls.objects.all()
        if configs.count()==0:
            cls.objects.create()
        return configs[0]
    

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

    modified         = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shop_monitor_tradeextrainfo'
        



  