__author__ = 'yann'
# -*- coding:utf-8 -*-
from django.db import models
from shopapp.weixin.models import WXOrder
from flashsale.xiaolumm.models import Clicks, XiaoluMama, AgencyLevel
import datetime


class StatisticsShopping(models.Model):
    
    linkid = models.IntegerField(default=0, verbose_name=u"链接ID")
    linkname = models.CharField(max_length=20, default="", verbose_name=u'代理人')
    openid = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u"OpenId")
    wxorderid = models.CharField(max_length=64, db_index=True, verbose_name=u'微信订单')
    wxordernick = models.CharField(max_length=32, verbose_name=u'购买昵称')
    wxorderamount = models.IntegerField(default=0, verbose_name=u'微信订单价格')
    tichengcount = models.IntegerField(default=0, verbose_name=u'提成')
    shoptime = models.DateTimeField(default=datetime.datetime.now, db_index=True, verbose_name=u'提成时间')
    
    class Meta:
        db_table = 'flashsale_tongji_shopping'
        unique_together = ('linkid', 'wxorderid')
        app_label = 'xiaolumm'
        verbose_name = u'统计购买'
        verbose_name_plural = u'统计购买列表'


    def order_cash(self):
        return self.wxorderamount / 100.0

    order_cash.allow_tags = True
    order_cash.short_description = u"订单金额"


    def ticheng_cash(self):
        return self.tichengcount / 100.0

    ticheng_cash.allow_tags = True
    ticheng_cash.short_description = u"提成金额"


class StatisticsShoppingByDay(models.Model):
    
    linkid = models.IntegerField(default=0, verbose_name=u"链接ID")
    linkname = models.CharField(max_length=20, default="", verbose_name=u'代理人')
    buyercount = models.IntegerField(default=0, verbose_name=u'购买人数')
    ordernumcount = models.IntegerField(default=0, verbose_name=u'订单总数')
    orderamountcount = models.IntegerField(default=0, verbose_name=u'订单总价')
    todayamountcount = models.IntegerField(default=0, verbose_name=u'提成总数')
    tongjidate = models.DateField(db_index=True,verbose_name=u'统计的日期')

    class Meta:
        db_table = 'flashsale_tongji_shopping_day'
        unique_together = ('linkid', 'tongjidate')
        app_label = 'xiaolumm'
        verbose_name = u'统计购买(按天)'
        verbose_name_plural = u'统计购买(按天)列表'


    def order_cash(self):
        return float(self.orderamountcount) / 100

    order_cash.allow_tags = True
    order_cash.short_description = u"今日订单总价"

    def today_cash(self):
        return self.todayamountcount / 100.0 

    today_cash.allow_tags = True
    today_cash.short_description = u"提成总价"
    

from django.db.models import F
from shopapp import signals

def tongji(sender, obj, **kwargs):
    
    today = datetime.date.today()
    target_time = obj.order_create_time.date()
    if target_time > today:
        target_time = today

    ordertime = obj.order_create_time
    order_stat_from = ordertime - datetime.timedelta(days=1)
    time_from = datetime.datetime(target_time.year,target_time.month,target_time.day,0,0,0)
    time_dayend  = datetime.datetime(target_time.year,target_time.month,target_time.day,23,59,59) 
    isinxiaolumm = XiaoluMama.objects.filter(openid=obj.buyer_openid,created__gt=ordertime)
    
    if isinxiaolumm.count() > 0:
        xiaolumm = isinxiaolumm[0]
        mm_order_rebeta     =  obj.order_total_price
        tongjiorder,state   = StatisticsShopping.objects.get_or_create(linkid=xiaolumm.id,
                                                               wxorderid=str(obj.order_id))
        tongjiorder.linkname      = xiaolumm.weikefu
        tongjiorder.openid        = obj.buyer_openid
        tongjiorder.wxordernick   = obj.buyer_nick
        tongjiorder.wxorderamount = mm_order_rebeta
        tongjiorder.shoptime      = obj.order_create_time
        tongjiorder.tichengcount  = mm_order_rebeta
        tongjiorder.save()
        
        daytongji,state = StatisticsShoppingByDay.objects.get_or_create(linkid=xiaolumm.id, 
                                                                        tongjidate=target_time)
        daytongji.linkname = xiaolumm.weikefu
        daytongji.ordernumcount    = F('ordernumcount') + 1
        daytongji.orderamountcount = F('orderamountcount') + mm_order_rebeta
        daytongji.todayamountcount = F('todayamountcount') + mm_order_rebeta
        daytongji.save()
        
        buyercount = StatisticsShopping.objects.filter(linkid=xiaolumm.id,
                            shoptime__range=(time_from, time_dayend)).values('openid').distinct().count()
        if buyercount != daytongji.buyercount:
            StatisticsShoppingByDay.objects.filter(linkid=xiaolumm.id, 
                                               tongjidate=target_time).update(buyercount=buyercount)
        return
    
    mm_clicks = Clicks.objects.filter(click_time__range=(order_stat_from, ordertime)).filter(
        openid=obj.buyer_openid).order_by('-created')
    if mm_clicks.count() > 0:
        mm_linkid   = mm_clicks[0].linkid
        mm_order_rebeta =  obj.order_total_price
        
        xiaolu_mmset = XiaoluMama.objects.filter(id=mm_linkid)
        if xiaolu_mmset.count() > 0:
            xiaolu_mm = xiaolu_mmset[0]
            tongjiorder,state = StatisticsShopping.objects.get_or_create(linkid=mm_linkid,
                                                                   wxorderid=str(obj.order_id))
            tongjiorder.linkname = xiaolu_mm.weikefu
            tongjiorder.openid = obj.buyer_openid
            tongjiorder.wxordernick = obj.buyer_nick
            tongjiorder.wxorderamount = mm_order_rebeta
            tongjiorder.shoptime = obj.order_create_time
            tongjiorder.tichengcount = mm_order_rebeta
            tongjiorder.save()
             
            daytongji,state = StatisticsShoppingByDay.objects.get_or_create(linkid=mm_linkid,
                                                      tongjidate=target_time)
            daytongji.linkname   = xiaolu_mm.weikefu
            daytongji.ordernumcount    = F('ordernumcount') + 1
            daytongji.orderamountcount = F('orderamountcount') + mm_order_rebeta
            daytongji.todayamountcount = F('todayamountcount') + mm_order_rebeta
            daytongji.save()
             
            buyercount = StatisticsShopping.objects.filter(linkid=xiaolu_mm.id,
                        shoptime__range=(time_from, time_dayend)).values('openid').distinct().count()
            if buyercount != daytongji.buyercount:
                StatisticsShoppingByDay.objects.filter(linkid=xiaolu_mm.id, 
                                                   tongjidate=target_time).update(buyercount=buyercount)
     
        else:
            StatisticsShopping(linkid=0, openid=obj.buyer_openid, 
                               wxorderid=str(obj.order_id),
                               wxorderamount=obj.order_total_price,
                               shoptime=obj.order_create_time, 
                               tichengcount=obj.order_total_price).save()
 
    else:
        tongjiorder,state = StatisticsShopping.objects.get_or_create(linkid=0, wxorderid=str(obj.order_id))
        tongjiorder.openid = obj.buyer_openid
        tongjiorder.wxorderamount = obj.order_total_price
        tongjiorder.shoptime = obj.order_create_time
        tongjiorder.tichengcount=obj.order_total_price
        tongjiorder.save()

    

signals.signal_wxorder_pay_confirm.connect(tongji, sender=WXOrder)

