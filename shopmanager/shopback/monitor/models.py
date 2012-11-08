#-*- coding:utf8 -*-
__author__ = 'meixqhi'
from django.db import models

class SystemConfig(models.Model):
    
    is_rule_auto = models.BooleanField(default=False)   #是否开启自动规则过滤
    is_sms_auto  = models.BooleanField(default=False)   #是否开启自动短信提醒
    
    is_flag_auto = models.BooleanField(default=False)   #是否将系统状态同步到淘宝旗帜颜色标识
    is_confirm_delivery_auto = models.BooleanField(default=False) #是否自动确认发货
    
    category_updated  = models.DateTimeField(null=True,blank=True)  #类目更新日期
    
    mall_order_updated  = models.DateTimeField(null=True,blank=True)  #商城订单更新日期  
    fenxiao_order_updated = models.DateTimeField(null=True,blank=True)  #分销订单更新日期
    
    
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
 
 
NEW_MEMO_CODE = 1     #新留言
NEW_REFUND_CODE = 2   #新退款
NEW_MERGE_TRADE_CODE = 3  #新合单
WAITING_REFUND_CODE = 4   #申请退款中
RULE_MATCH_CODE = 5   #有规则匹配
OUT_GOOD_CODE = 6   #订单缺货
INVALID_END_CODE = 7  #订单非正常结束
POST_MODIFY_CODE = 8 #订单有改动
POST_SUB_TRADE_ERROR_CODE = 9 #子订单发货失败，请检查子订单是否退款,(如退款拆包并保留父订单物流单)
COMPOSE_RULE_ERROR_CODE = 10 #组合商品拆分出错 
MULTIPLE_ORDERS_CODE = 11 #买家有多单等待合并 



class Reason(models.Model):
    #问题理由
    id  = models.AutoField(primary_key=True)
    reason_text = models.TextField(max_length=64,verbose_name='问题原因')
    priority    = models.IntegerField(default=0,verbose_name='优先级')
    created     = models.DateTimeField(auto_now=True,verbose_name='创建日期')
    
    class Meta:
        db_table = 'shop_monitor_reason'
        verbose_name='订单问题'
  
