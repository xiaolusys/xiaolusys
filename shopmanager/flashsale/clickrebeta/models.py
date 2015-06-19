__author__ = 'yann'
# -*- coding:utf-8 -*-
from django.db import models
from shopapp.weixin.models import WXOrder
from flashsale.xiaolumm.models import Clicks, XiaoluMama, AgencyLevel,CarryLog
import datetime

class NormalShopingManager(models.Manager):

    def get_queryset(self):
        
        super_tm = super(NormalShopingManager,self)
        #adapt to higer version django(>1.4)
        if hasattr(super_tm,'get_query_set'):
            return super_tm.get_query_set().filter(status__in=self.model.NORMAL_STATUS)
        
        return super_tm.get_queryset().filter(status__in=self.model.NORMAL_STATUS)

class StatisticsShopping(models.Model):
    
    WAIT_SEND = 0
    FINISHED  = 1
    REFUNDED  = 2
    
    SHOPPING_STATUS = (
        (WAIT_SEND, u'已付款'),       
        (FINISHED, u'已完成'),
        (REFUNDED, u'已退款'),
    )
    
    NORMAL_STATUS = [WAIT_SEND,FINISHED]
    
    linkid = models.IntegerField(default=0,verbose_name=u"链接ID")
    linkname = models.CharField(max_length=20, default="", verbose_name=u'代理人')
    openid = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u"OpenId")
    wxorderid = models.CharField(max_length=64, db_index=True, verbose_name=u'微信订单')
    wxordernick = models.CharField(max_length=32, verbose_name=u'购买昵称')
    wxorderamount = models.IntegerField(default=0, verbose_name=u'微信订单价格')
    tichengcount = models.IntegerField(default=0, verbose_name=u'提成')
    shoptime = models.DateTimeField(default=datetime.datetime.now, db_index=True, verbose_name=u'提成时间')
    status   = models.IntegerField(default=0, choices=SHOPPING_STATUS, verbose_name=u'订单状态')
    
    objects = models.Manager()
    normal_objects = NormalShopingManager()
    
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
    
    @property
    def status_name(self):
        return self.get_status_display()


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
    
    def carry_Confirm(self):
        c_logs = CarryLog.objects.filter(xlmm=self.linkid,
                                         log_type=CarryLog.ORDER_REBETA,
                                         carry_date=self.tongjidate,
                                         status=CarryLog.CONFIRMED)
        return c_logs.count() > 0
    

from django.db.models import F
from django.conf import settings
from shopapp import signals
from shopapp.weixin.models import get_Unionid

def tongji_wxorder(sender, obj, **kwargs):
    """ 统计微信小店订单订单提成信息 """
    today = datetime.date.today()
    target_time = obj.order_create_time.date()
    if target_time > today:
        target_time = today

    ordertime = obj.order_create_time
    order_stat_from = ordertime - datetime.timedelta(days=1)
    time_from = datetime.datetime(target_time.year,target_time.month,target_time.day,0,0,0)
    time_dayend  = datetime.datetime(target_time.year,target_time.month,target_time.day,23,59,59) 
    
    wx_unionid = get_Unionid(obj.buyer_openid,settings.WEIXIN_APPID)
    isinxiaolumm = XiaoluMama.objects.filter(openid=wx_unionid,agencylevel=2,
                                             charge_time__lte=ordertime)
    
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
        openid=obj.buyer_openid).order_by('-click_time')
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

    

signals.signal_wxorder_pay_confirm.connect(tongji_wxorder, sender=WXOrder)

from flashsale.pay.models import SaleTrade
from shopapp.weixin.models import WeixinUnionID
from flashsale.pay.signals import signal_saletrade_pay_confirm

def tongji_saleorder(sender, obj, **kwargs):
    """ 统计特卖订单提成 """
    #如果订单试用钱包付款，或是押金订单则不处理
    if obj.channel == SaleTrade.WALLET or obj.is_Deposite_Order():
        return 
    
    today = datetime.date.today()
    target_time = obj.pay_time.date()
    if target_time > today:
        target_time = today

    buyer_openid = obj.openid
    mm_order_rebeta   =  int(obj.payment * 100)
    order_id     = obj.tid
    ordertime    = obj.pay_time
    order_stat_from = ordertime - datetime.timedelta(days=1)
    time_from = datetime.datetime(target_time.year,target_time.month,target_time.day,0,0,0)
    time_dayend  = datetime.datetime(target_time.year,target_time.month,target_time.day,23,59,59) 
    
    wx_unionid = get_Unionid(buyer_openid,settings.WXPAY_APPID)
    if not wx_unionid:
        return
    
    xd_unoins  = WeixinUnionID.objects.filter(unionid=wx_unionid,app_key=settings.WEIXIN_APPID) #小店openid
    xd_openid  = wx_unionid
    if xd_unoins.count() > 0:
        xd_openid = xd_unoins[0].openid
        
    isinxiaolumm = XiaoluMama.objects.filter(openid=wx_unionid,agencylevel=2,
                                             charge_time__lte=ordertime)
    
    if isinxiaolumm.count() > 0:
        xiaolumm = isinxiaolumm[0]
        tongjiorder,state   = StatisticsShopping.objects.get_or_create(linkid=xiaolumm.id,
                                                               wxorderid=order_id)
        tongjiorder.linkname      = xiaolumm.weikefu
        tongjiorder.openid        = xd_openid
        tongjiorder.wxordernick   = obj.buyer_nick
        tongjiorder.wxorderamount = mm_order_rebeta
        tongjiorder.shoptime      = ordertime
        tongjiorder.tichengcount  = mm_order_rebeta
        tongjiorder.save()
        
        daytongji,state = StatisticsShoppingByDay.objects.get_or_create(linkid=xiaolumm.id, 
                                                                        tongjidate=target_time)
        daytongji.linkname         = xiaolumm.weikefu
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
        openid=xd_openid).order_by('-click_time')
    if mm_clicks.count() > 0:
        mm_linkid   = mm_clicks[0].linkid
        xiaolu_mmset = XiaoluMama.objects.filter(id=mm_linkid)
        if xiaolu_mmset.count() > 0:
            xiaolu_mm = xiaolu_mmset[0]
            tongjiorder,state = StatisticsShopping.objects.get_or_create(linkid=mm_linkid,
                                                                   wxorderid=order_id)
            tongjiorder.linkname    = xiaolu_mm.weikefu
            tongjiorder.openid      = xd_openid
            tongjiorder.wxordernick = obj.buyer_nick
            tongjiorder.wxorderamount = mm_order_rebeta
            tongjiorder.shoptime      = ordertime
            tongjiorder.tichengcount  = mm_order_rebeta
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
            StatisticsShopping(linkid=0, 
                               openid=xd_openid, 
                               wxorderid=order_id,
                               wxorderamount=mm_order_rebeta,
                               shoptime=ordertime, 
                               tichengcount=mm_order_rebeta).save()
 
    else:
        tongjiorder,state = StatisticsShopping.objects.get_or_create(linkid=0, wxorderid=order_id)
        tongjiorder.openid = xd_openid
        tongjiorder.wxorderamount = mm_order_rebeta
        tongjiorder.shoptime = ordertime
        tongjiorder.tichengcount=mm_order_rebeta
        tongjiorder.save()
    
signal_saletrade_pay_confirm.connect(tongji_saleorder, sender=SaleTrade)


