#-*- coding:utf8 -*-
__author__ = 'meixqhi'
from django.db import models

class SystemConfig(models.Model):
    
    is_rule_auto = models.BooleanField(default=False,verbose_name='商品匹配')   #是否开启自动规则过滤
    is_sms_auto  = models.BooleanField(default=False,verbose_name='短信提醒')   #是否开启自动短信提醒
    is_flag_auto = models.BooleanField(default=False,verbose_name='同步淘宝旗帜')   #是否将系统状态同步到淘宝旗帜颜色标识
    
    client_num   = models.IntegerField(default=1,verbose_name='客户端数量')
    category_updated  = models.DateTimeField(null=True,blank=True,verbose_name='类目更新日期')  #类目更新日期
    
    mall_order_updated  = models.DateTimeField(null=True,blank=True,verbose_name='商城订单更新日期')  #商城订单更新日期  
    fenxiao_order_updated = models.DateTimeField(null=True,blank=True,verbose_name='分销订单更新日期')  #分销订单更新日期
    
    
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
    #订单财务及物流单是否更新
    tid   =  models.BigIntegerField(primary_key=True)

    is_update_amount = models.BooleanField(default=False)
    is_update_logistic = models.BooleanField(default=False)

    modified         = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shop_monitor_tradeextrainfo'
 


class Reason(models.Model):
    #问题理由
    id  = models.AutoField(primary_key=True)
    reason_text = models.TextField(max_length=64,verbose_name='问题原因')
    priority    = models.IntegerField(default=0,verbose_name='优先级')
    created     = models.DateTimeField(auto_now=True,verbose_name='创建日期')
    
    class Meta:
        db_table = 'shop_monitor_reason'
        verbose_name='订单问题'
  

