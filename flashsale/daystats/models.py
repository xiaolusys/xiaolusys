# -*- coding:utf-8 -*-
import datetime
from django.db import models


class DailyStat(models.Model):
    total_click_count = models.IntegerField(default=0, verbose_name=u'日点击数')
    total_valid_count = models.IntegerField(default=0, verbose_name=u'日有效点击数')
    total_visiter_num = models.IntegerField(default=0, verbose_name=u'日访客数')
    total_new_visiter_num = models.IntegerField(default=0, verbose_name=u'新访客数')

    total_payment = models.IntegerField(default=0, verbose_name=u'日成交额')
    total_paycash = models.IntegerField(default=0, verbose_name=u'实付现金')
    total_coupon  = models.IntegerField(default=0, verbose_name=u'券使用额')
    total_budget  = models.IntegerField(default=0, verbose_name=u'钱包余额')
    total_boutique = models.IntegerField(default=0, verbose_name=u'购精品券')
    total_deposite  = models.IntegerField(default=0, verbose_name=u'支付押金')

    total_order_num = models.IntegerField(default=0, verbose_name=u'日订单数')
    total_buyer_num = models.IntegerField(default=0, verbose_name=u'日购买人数')
    total_old_buyer_num = models.IntegerField(default=0, verbose_name=u'老成交人数')
    total_new_order_num = models.IntegerField(default=0, verbose_name=u'新用户单数')
    seven_buyer_num = models.IntegerField(default=0, verbose_name=u'七日老成交人数')

    #     page_view_count   = models.IntegerField(verbose_name=u'商品浏览量数')
    #     shelf_view_count   = models.IntegerField(verbose_name=u'首页浏览量数')

    day_date = models.DateField(verbose_name=u'统计日期')

    class Meta:
        db_table  = 'flashsale_dailystat'
        app_label = 'daystats'
        verbose_name = u'特卖/每日统计'
        verbose_name_plural = u'特卖/每日统计列表'

    @property
    def total_payment_cash(self):

        if not self.total_payment:
            return 0
        return self.total_payment

    def get_seven_new_buyer_num(self):
        return self.total_buyer_num - self.seven_buyer_num

    get_seven_new_buyer_num.allow_tags = True
    get_seven_new_buyer_num.short_description = u"七日新成交人数"

    def get_total_payment_display(self):
        return self.total_payment_cash / 100.0

    get_total_payment_display.allow_tags = True
    get_total_payment_display.short_description = u"日成交额"

    @property
    def price_per_customer(self):
        if not self.total_buyer_num:
            return 0
        return round(self.total_payment / float(self.total_buyer_num), 2)

    def get_price_per_customer_display(self):
        return self.price_per_customer / 100.0

    get_price_per_customer_display.allow_tags = True
    get_price_per_customer_display.short_description = u"客单价"

    def get_new_customer_num_display(self):
        return self.total_buyer_num - self.total_old_buyer_num

    get_new_customer_num_display.allow_tags = True
    get_new_customer_num_display.short_description = u"新购买用户数"

    @property
    def daily_roi(self):
        if not self.total_visiter_num:
            return 0
        return round(self.total_buyer_num / float(self.total_visiter_num), 4)

    def get_daily_roi_display(self):
        return self.daily_roi

    get_daily_roi_display.allow_tags = True
    get_daily_roi_display.short_description = u"日转化率"

    @property
    def daily_rpi(self):
        if not self.total_old_buyer_num:
            return 0
        return round(self.total_old_buyer_num / float(self.total_buyer_num), 2)

    def get_daily_rpi_display(self):
        return self.daily_rpi

    get_daily_rpi_display.allow_tags = True
    get_daily_rpi_display.short_description = u"回头客比例"


class PopularizeCost(models.Model):
    date = models.DateField(default=datetime.date.today, db_index=True, unique=True, verbose_name=u'业务日期')
    carrylog_order = models.FloatField(default=0.0, db_index=True, verbose_name=u"订单返利")
    carrylog_click = models.FloatField(default=0.0, db_index=True, verbose_name=u"点击补贴")
    carrylog_thousand = models.FloatField(default=0.0, db_index=True, verbose_name=u"千元提成")
    carrylog_agency = models.FloatField(default=0.0, db_index=True, verbose_name=u"代理补贴")
    carrylog_recruit = models.FloatField(default=0.0, db_index=True, verbose_name=u"招募奖金")

    carrylog_order_buy = models.FloatField(default=0.0, db_index=True, verbose_name=u"消费支出")
    carrylog_cash_out = models.FloatField(default=0.0, db_index=True, verbose_name=u"钱包提现")
    carrylog_deposit = models.FloatField(default=0.0, db_index=True, verbose_name=u"押金")
    carrylog_refund_return = models.FloatField(default=0.0, db_index=True, verbose_name=u"退款返现")
    carrylog_red_packet = models.FloatField(default=0.0, verbose_name=u"订单红包")

    total_carry_in = models.FloatField(default=0.0, db_index=True, verbose_name=u"推广费用")
    total_carry_out = models.FloatField(default=0.0, db_index=True, verbose_name=u"妈妈支出")

    class Meta:
        db_table = 'flashsale_daily_popularize_cost'
        app_label = 'daystats'
        verbose_name = u'每日推广支出'
        verbose_name_plural = u'每日推广支出列表'

    def total_incarry(self):
        return self.carrylog_order + self.carrylog_click + self.carrylog_thousand + self.carrylog_agency + self.carrylog_recruit + self.carrylog_red_packet

    total_incarry.short_description = u'推广费用'

    def total_outcarry(self):
        return self.carrylog_order_buy + self.carrylog_cash_out

    total_outcarry.short_description = u'妈妈支出'


from core.fields import JSONCharMyField
from core.models import BaseModel


class DaystatCalcResult(BaseModel):
    calc_key = models.CharField(max_length=128, db_index=True, verbose_name=u"计算结果ID")

    calc_result = JSONCharMyField(max_length=102400, default={}, blank=False, verbose_name=u"计算结果ID")

    class Meta:
        db_table = 'flashsale_daystat_result_cache'
        app_label = 'daystats'
        verbose_name = u'小鹿妈妈／数据统计暂存结果'
        verbose_name_plural = u'小鹿妈妈／数据统计暂存结果'
