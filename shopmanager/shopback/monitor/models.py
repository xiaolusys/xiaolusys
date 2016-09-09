# -*- coding:utf-8 -*-
__author__ = 'meixqhi'
from django.db import models
import datetime

class SystemConfig(models.Model):
    is_rule_auto = models.BooleanField(default=False, verbose_name='商品匹配')  # 是否开启自动规则过滤
    is_sms_auto = models.BooleanField(default=False, verbose_name='短信提醒')  # 是否开启自动短信提醒
    is_flag_auto = models.BooleanField(default=False, verbose_name='同步旗帜')  # 是否将系统状态同步到淘宝旗帜颜色标识

    storage_num_to_stock_auto = models.BooleanField(default=False, verbose_name='确认入库数自动入库存')
    purchase_price_to_cost_auto = models.BooleanField(default=False, verbose_name='采购进价自动同步成本')

    normal_print_limit = models.BooleanField(default=True, verbose_name='单打模式连打')  # 单打模式是否能连打
    per_request_num = models.IntegerField(default=30, verbose_name='最大单次锁定单数')
    client_num = models.IntegerField(default=1, verbose_name='客户端数量')

    jhs_logistic_code = models.CharField(blank=True, null=True, max_length=20, verbose_name='聚划算指定快递')

    category_updated = models.DateTimeField(null=True, blank=True, verbose_name='类目更新日期')  # 类目更新日期
    mall_order_updated = models.DateTimeField(null=True, blank=True, verbose_name='商城订单更新日期')  # 商城订单更新日期
    fenxiao_order_updated = models.DateTimeField(null=True, blank=True, verbose_name='分销订单更新日期')  # 分销订单更新日期

    class Meta:
        db_table = 'shop_monitor_systemconfig'
        app_label = 'monitor'
        verbose_name = u'系统设置'
        verbose_name_plural = u'系统设置'

    @classmethod
    def getconfig(cls):
        configs = cls.objects.all()
        if configs.count() == 0:
            cls.objects.create()
        return configs[0]


class DayMonitorStatus(models.Model):
    user_id = models.CharField(max_length=64)
    year = models.IntegerField()
    month = models.IntegerField()
    day = models.IntegerField()

    update_trade_increment = models.BooleanField(default=False)
    update_purchase_increment = models.BooleanField(default=False)

    class Meta:
        db_table = 'shop_monitor_daymonitortatus'
        unique_together = ("user_id", "year", "month", "day")
        app_label = 'monitor'
        verbose_name = u'店铺更新状态'
        verbose_name_plural = u'店铺更新状态列表'


class TradeExtraInfo(models.Model):
    # 订单财务及物流单是否更新
    tid = models.BigIntegerField(primary_key=True)

    is_update_amount = models.BooleanField(default=False)
    is_update_logistic = models.BooleanField(default=False)

    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shop_monitor_tradeextrainfo'
        app_label = 'monitor'
        verbose_name = u'交易更新状态'
        verbose_name_plural = u'交易更新状态'


class Reason(models.Model):
    # 订单问题
    id = models.AutoField(primary_key=True)
    reason_text = models.TextField(max_length=64, verbose_name='问题原因')
    priority = models.IntegerField(default=0, verbose_name='优先级')
    created = models.DateTimeField(auto_now=True, verbose_name='创建日期')

    class Meta:
        db_table = 'shop_monitor_reason'
        app_label = 'monitor'
        verbose_name = u'订单问题'
        verbose_name_plural = u'订单问题列表'


from core.models import BaseModel

class XiaoluSwitch(BaseModel):
    STATUS_TYPES = ((0, u'取消'), (1, u'生效'))
    
    start_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'生效时间')
    end_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'结束时间')
    responsible = models.CharField(max_length=32, db_index=True, verbose_name=u'负责人')
    title = models.CharField(max_length=64, db_index=True, verbose_name=u'标题')
    description = models.TextField(verbose_name=u'描述')
    status = models.IntegerField(default=0, choices=STATUS_TYPES, db_index=True, verbose_name=u'状态')

    class Meta:
        db_table = 'xiaolu_switch'
        app_label = 'monitor'
        verbose_name = u'开关器'
        verbose_name_plural = u'开关器列表'

    @classmethod
    def is_switch_open(cls, id):
        switch = cls.objects.get(id=id)
        now = datetime.datetime.now()
        if switch.status == 1:
            if now >= self.start_time and now <= self.end_time:
                return True
        return False
        
        
