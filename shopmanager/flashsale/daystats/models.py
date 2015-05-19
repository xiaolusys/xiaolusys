__author__ = 'yann'
# -*- coding:utf-8 -*-
from django.db import models
from shopapp.weixin.models import WXOrder
from flashsale.xiaolumm.models import Clicks, XiaoluMama, AgencyLevel
import datetime


class DailyStat(models.Model):
    
    total_click_count = models.IntegerField(verbose_name=u'日点击数')
    total_valid_count = models.IntegerField(verbose_name=u'日有效点击数')
    total_visiter_num = models.IntegerField(verbose_name=u'日访客数')
    
    total_payment     = models.IntegerField(verbose_name=u'日成交额')
    total_order_num   = models.IntegerField(verbose_name=u'日订单数')
    total_buyer_num   = models.IntegerField(verbose_name=u'日购买人数')
    total_old_buyer_num   = models.IntegerField(verbose_name=u'日回头客数')
    
    day_date = models.DateField(auto_now_add=True, verbose_name=u'统计日期')
    
    class Meta:
        db_table = 'flashsale_dailystat'
        app_label = 'xiaolumm'
        verbose_name = u'特卖/每日统计'
        verbose_name_plural = u'特卖/每日统计列表'
    
    def total_payment_cash(self):
        return self.total_payment / 100.0

    def get_pice_per_customer_display(self):
        if not self.total_buyer_num:
            return 0
        return round(self.total_payment / float(self.total_buyer_num),2)

    get_pice_per_customer_display.allow_tags = True
    get_pice_per_customer_display.short_description = u"客单价"
    
    @property
    def pice_per_customer(self):
        return self.get_pice_per_customer_display()

    def get_daily_roi_display(self):
        if not self.total_visiter_num:
            return 0
        return round(self.total_buyer_num / float(self.total_visiter_num),2)

    get_daily_roi_display.allow_tags = True
    get_daily_roi_display.short_description = u"日转化率"
    
    @property
    def daily_roi(self):
        return self.get_daily_roi_display()
    
    
    