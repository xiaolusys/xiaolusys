__author__ = 'yann'
# -*- coding:utf-8 -*-
from django.db import models
from shopapp.weixin.models import WXOrder
from flashsale.xiaolumm.models import Clicks, XiaoluMama
import datetime

class StatisticsShopping(models.Model):
    linkid = models.IntegerField(default=0, db_index=True, verbose_name=u"链接ID")
    linkname = models.CharField(max_length=20, default="", verbose_name=u'代理人')
    openid = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u"OpenId")
    wxorderid = models.CharField(max_length=64, db_index=True, verbose_name=u'微信订单')
    wxorderamount = models.IntegerField(default=0, verbose_name=u'微信订单价格')
    tichengcount = models.IntegerField(default=0, verbose_name=u'提成')
    shoptime = models.DateTimeField(auto_now_add=True, verbose_name=u'提成时间')

    class Meta:
        db_table = 'flashsale_tongji_shopping'
        verbose_name = u'统计购买'
        verbose_name_plural = u'统计购买列表'

    @property
    def ticheng_rate(self):
        return 0.1


    def order_cash(self):
        return float(self.wxorderamount) / 100

    order_cash.allow_tags = True
    order_cash.short_description = u"订单价格"


    def ticheng_cash(self):
        return (float(self.tichengcount) / 100) * self.ticheng_rate

    ticheng_cash.allow_tags = True
    ticheng_cash.short_description = u"提成"

class StatisticsShoppingByDay(models.Model):
    linkid = models.IntegerField(default=0, db_index=True, verbose_name=u"链接ID")
    linkname = models.CharField(max_length=20, default="", verbose_name=u'代理人')
    ordernumcount = models.IntegerField(default=0, verbose_name=u'订单总数')
    orderamountcount = models.IntegerField(default=0, verbose_name=u'订单总价')
    todayamountcount = models.IntegerField(default=0, verbose_name=u'提成总数')
    tongjidate = models.DateField(verbose_name=u'统计的日期')


    class Meta:
        db_table = 'flashsale_tongji_shopping_day'
        verbose_name = u'按天统计购买'
        verbose_name_plural = u'按天统计购买列表'


    @property
    def ticheng_rate(self):
        return 0.1

    @property
    def order_cash(self):
        return self.orderamountcount / 100

    @property
    def today_cash(self):
        return (self.todayamountcount / 100) * self.ticheng_rate

from shopapp import signals

def tongji(sender, obj, **kwargs):
    
    today = datetime.date.today()
    target_time = obj.order_create_time
    target_time = datetime.date(target_time.year, target_time.month, target_time.day)
    if target_time > today:
        target_time = today
    is_today = False
    if (today == target_time):
        is_today = True

    ordertime = obj.order_create_time
    time_from = ordertime - datetime.timedelta(days=1)
    clicksbetwwentime = Clicks.objects.filter(created__range=(time_from, ordertime)).filter(
        openid=obj.buyer_openid).values('linkid').distinct()
    if clicksbetwwentime:
        length = clicksbetwwentime.count()
        for s in clicksbetwwentime:
            xiaolu_mmset = XiaoluMama.objects.filter(id=s['linkid'])
            if xiaolu_mmset.count() > 0:
                xiaolu_mm = xiaolu_mmset[0]
                StatisticsShopping(linkid=s['linkid'], linkname=xiaolu_mm.weikefu, openid=obj.buyer_openid,
                                   wxorderid=str(obj.order_id),
                                   wxorderamount=obj.order_total_price,
                                   shoptime=obj.order_create_time, tichengcount=obj.order_total_price / length).save()
                if is_today:
                    daytongji = StatisticsShoppingByDay.objects.get_or_create(linkid=s['linkid'],
                                                                              tongjidate=target_time)
                    daytongji[0].ordernumcount = daytongji[0].ordernumcount + 1
                    daytongji[0].orderamountcount = daytongji[0].orderamountcount + obj.order_total_price
                    daytongji[0].todayamountcount = daytongji[0].todayamountcount + obj.order_total_price / length
                    daytongji[0].save()
            else:
                StatisticsShopping(linkid=0, openid=obj.buyer_openid, wxorderid=str(obj.order_id),
                           wxorderamount=obj.order_total_price,
                           shoptime=obj.order_create_time, tichengcount=0).save()


    else:
        StatisticsShopping(linkid=0, openid=obj.buyer_openid, wxorderid=str(obj.order_id),
                           wxorderamount=obj.order_total_price,
                           shoptime=obj.order_create_time, tichengcount=0).save()


signals.signal_wxorder_pay_confirm.connect(tongji, sender=WXOrder)

