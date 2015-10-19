__author__ = 'yann'
# -*- coding:utf-8 -*-
from django.db import models
from shopapp.weixin.models import WXOrder
from flashsale.xiaolumm.models import Clicks, XiaoluMama, AgencyLevel,CarryLog
import datetime

CLICK_VALID_DAYS = 2

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
        (REFUNDED, u'已取消'),
    )
    
    NORMAL_STATUS = [WAIT_SEND,FINISHED]
    
    linkid    = models.IntegerField(default=0,verbose_name=u"链接ID")
    linkname  = models.CharField(max_length=20, default="", verbose_name=u'代理人')
    openid    = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u"优尼OpenId")
    wxorderid = models.CharField(max_length=64, db_index=True, verbose_name=u'微信订单')
    wxordernick   = models.CharField(max_length=32, verbose_name=u'购买昵称')
    wxorderamount = models.IntegerField(default=0, verbose_name=u'微信订单价格')
    rebetamount   = models.IntegerField(default=0, verbose_name=u'有效金额')
    tichengcount  = models.IntegerField(default=0, verbose_name=u'订单提成')
    shoptime = models.DateTimeField(default=datetime.datetime.now, db_index=True, verbose_name=u'提成时间')
    status   = models.IntegerField(default=WAIT_SEND, choices=SHOPPING_STATUS, verbose_name=u'订单状态')
    
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
    
    def rebeta_cash(self):
        return self.wxorderamount / 100.0

    rebeta_cash.allow_tags = True
    rebeta_cash.short_description = u"有效金额"

    def ticheng_cash(self):
        return self.tichengcount / 100.0

    ticheng_cash.allow_tags = True
    ticheng_cash.short_description = u"提成金额"
    
    @property
    def status_name(self):
        return self.get_status_display()
    
    def is_balanced(self):
        clogs = CarryLog.objects.filter(xlmm=self.linkid,
                                       log_type=CarryLog.ORDER_REBETA,
                                       carry_date=self.shoptime.date())
        if clogs.count() == 0:
            return False
        clog = clogs[0]
        return clog.status != CarryLog.PENDING
        

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
    
# 2015-08-24  取消首单十个单红包　之前发放的会在任务里面　予以确定
from django.db.models.signals import post_save

def check_or_create_order_redenvelop(sender,instance, **kwargs):

    from flashsale.xiaolumm.tasks import order_Red_Packet_Pending_Carry
    # 首单十单红包创建 2015-07-08 添加
    order_Red_Packet_Pending_Carry(instance.linkid, datetime.date.today())

post_save.connect(check_or_create_order_redenvelop, sender=StatisticsShoppingByDay)


def get_xlmm_linkid(click_set):
    ''' 根据点击获取小鹿妈妈ID '''
    exclude_xlmmids = (0,44)
    for cc in click_set:
        if cc.linkid in exclude_xlmmids:
            continue
        return cc.linkid
    return 44

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
    order_stat_from = ordertime - datetime.timedelta(days=CLICK_VALID_DAYS)
    time_from = datetime.datetime(target_time.year,target_time.month,target_time.day,0,0,0)
    time_dayend  = datetime.datetime(target_time.year,target_time.month,target_time.day,23,59,59) 
    mm_order_amount = obj.order_total_price
    mm_rebeta_amount = 0
    mm_order_rebeta = 0
    wx_unionid = get_Unionid(obj.buyer_openid,settings.WEIXIN_APPID)
    isinxiaolumm = XiaoluMama.objects.filter(openid=wx_unionid,
                                             charge_status=XiaoluMama.CHARGED,
                                             charge_time__lte=ordertime)
    
    if isinxiaolumm.count() > 0:
        xiaolumm = isinxiaolumm[0]
        #计算小鹿妈妈订单返利
        mm_rebeta_amount    = xiaolumm.get_Mama_Trade_Amount(obj) 
        mm_order_rebeta     = xiaolumm.get_Mama_Trade_Rebeta(obj) 
        tongjiorder,state   = StatisticsShopping.objects.get_or_create(linkid=xiaolumm.id,
                                                               wxorderid=str(obj.order_id))
        tongjiorder.linkname      = xiaolumm.weikefu
        tongjiorder.openid        = obj.buyer_openid
        tongjiorder.wxordernick   = obj.buyer_nick
        tongjiorder.wxorderamount = mm_order_amount
        tongjiorder.rebetamount   = mm_rebeta_amount
        tongjiorder.shoptime      = obj.order_create_time
        tongjiorder.tichengcount  = mm_order_rebeta
        tongjiorder.save()
        
        daytongji,state = StatisticsShoppingByDay.objects.get_or_create(linkid=xiaolumm.id, 
                                                                        tongjidate=target_time)
        daytongji.linkname = xiaolumm.weikefu
        daytongji.ordernumcount    = F('ordernumcount') + 1
        daytongji.orderamountcount = F('orderamountcount') + mm_order_amount
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
        mm_linkid   = get_xlmm_linkid(mm_clicks)
        mm_order_rebeta =  obj.order_total_price
        
        xiaolu_mmset = XiaoluMama.objects.filter(id=mm_linkid)
        if xiaolu_mmset.count() > 0:
            xiaolu_mm = xiaolu_mmset[0]
            #计算小鹿妈妈订单返利
            mm_rebeta_amount    = xiaolu_mm.get_Mama_Trade_Amount(obj) 
            mm_order_rebeta     = xiaolu_mm.get_Mama_Trade_Rebeta(obj) 
            tongjiorder,state = StatisticsShopping.objects.get_or_create(linkid=mm_linkid,
                                                                   wxorderid=str(obj.order_id))
            tongjiorder.linkname = xiaolu_mm.weikefu
            tongjiorder.openid = obj.buyer_openid
            tongjiorder.wxordernick = obj.buyer_nick
            tongjiorder.wxorderamount = mm_order_amount
            tongjiorder.rebetamount   = mm_rebeta_amount
            tongjiorder.shoptime = obj.order_create_time
            tongjiorder.tichengcount = mm_order_rebeta
            tongjiorder.save()
             
            daytongji,state = StatisticsShoppingByDay.objects.get_or_create(linkid=mm_linkid,
                                                      tongjidate=target_time)
            daytongji.linkname   = xiaolu_mm.weikefu
            daytongji.ordernumcount    = F('ordernumcount') + 1
            daytongji.orderamountcount = F('orderamountcount') + mm_order_amount
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
                               wxorderamount=mm_order_amount,
                               shoptime=obj.order_create_time, 
                               tichengcount=mm_order_rebeta).save()

    else:
        tongjiorder,state = StatisticsShopping.objects.get_or_create(linkid=0, wxorderid=str(obj.order_id))
        tongjiorder.openid = obj.buyer_openid
        tongjiorder.wxorderamount = mm_order_amount
        tongjiorder.shoptime = obj.order_create_time
        tongjiorder.tichengcount=mm_order_rebeta
        tongjiorder.save()

signals.signal_wxorder_pay_confirm.connect(tongji_wxorder, sender=WXOrder)

from flashsale.pay.models import SaleTrade,SaleOrder
from shopapp.weixin.models import WeixinUnionID
from flashsale.pay.signals import signal_saletrade_pay_confirm



def tongji_saleorder(sender, obj, **kwargs):
    """ 统计特卖订单提成 """
    #如果订单试用钱包付款，或是押金订单则不处理

    if obj.is_Deposite_Order():
        return 
    
    today = datetime.date.today()
    target_time = obj.pay_time.date()
    if target_time > today:
        target_time = today

    buyer_openid = obj.get_buyer_openid() 
    mm_order_amount   = int(obj.payment * 100)
    mm_order_rebeta	  = 0
    mm_rebeta_amount  = 0
    order_id          = obj.tid
    order_buyer_nick  = obj.buyer_nick or '%s(%s)'%(obj.receiver_name[0:24],obj.receiver_mobile[8:11])
    ordertime       = obj.pay_time
    order_stat_from = ordertime - datetime.timedelta(days=CLICK_VALID_DAYS)
    time_from = datetime.datetime(target_time.year,target_time.month,target_time.day,0,0,0)
    time_dayend  = datetime.datetime(target_time.year,target_time.month,target_time.day,23,59,59) 
    
    wx_unionid = get_Unionid(buyer_openid,settings.WXPAY_APPID)
    if not wx_unionid:
        wx_unionid = obj.receiver_mobile or str(obj.buyer_id)
    xd_unoins  = WeixinUnionID.objects.filter(unionid=wx_unionid,app_key=settings.WEIXIN_APPID) #小店openid
    xd_openid  = wx_unionid
    if xd_unoins.count() > 0:
        xd_openid = xd_unoins[0].openid
    #如果钱包付款，则不算提成
    if obj.channel == SaleTrade.WALLET or obj.pay_time < datetime.datetime(2015,6,19):
        StatisticsShopping(linkid=0, 
                           openid=xd_openid, 
                           wxorderid=order_id,
                           wxorderamount=mm_order_amount,
                           shoptime=ordertime, 
                           tichengcount=mm_order_rebeta).save()
        return
    
    isinxiaolumm = XiaoluMama.objects.filter(openid=wx_unionid,
                                             charge_status=XiaoluMama.CHARGED,
                                             charge_time__lte=ordertime)
    
    if isinxiaolumm.count() > 0:
        xiaolumm = isinxiaolumm[0]
        #计算小鹿妈妈订单返利
        mm_rebeta_amount    = xiaolumm.get_Mama_Trade_Amount(obj) 
        mm_order_rebeta     = xiaolumm.get_Mama_Trade_Rebeta(obj)
        tongjiorder,state   = StatisticsShopping.objects.get_or_create(linkid=xiaolumm.id,
                                                               wxorderid=order_id)
        tongjiorder.linkname      = xiaolumm.weikefu
        tongjiorder.openid        = xd_openid
        tongjiorder.wxordernick   = order_buyer_nick
        tongjiorder.wxorderamount = mm_order_amount
        tongjiorder.shoptime      = ordertime
        tongjiorder.tichengcount  = mm_order_rebeta
        tongjiorder.rebetamount   = mm_rebeta_amount
        tongjiorder.save()
        
        daytongji,state = StatisticsShoppingByDay.objects.get_or_create(linkid=xiaolumm.id, 
                                                                        tongjidate=target_time)
        daytongji.linkname         = xiaolumm.weikefu
        daytongji.ordernumcount    = F('ordernumcount') + 1
        daytongji.orderamountcount = F('orderamountcount') + mm_order_amount
        daytongji.todayamountcount = F('todayamountcount') + mm_order_rebeta
        daytongji.save()

        buyercount = StatisticsShopping.objects.filter(linkid=xiaolumm.id,
                            shoptime__range=(time_from, time_dayend)).values('openid').distinct().count()
        if buyercount != daytongji.buyercount:
            StatisticsShoppingByDay.objects.filter(linkid=xiaolumm.id, 
                                               tongjidate=target_time).update(buyercount=buyercount)
        return
    
    mm_clicks = Clicks.objects.filter(click_time__range=(order_stat_from, ordertime)).filter(
        openid=xd_openid).order_by('-click_time')#去掉0，44对应的小鹿妈妈ID
    if mm_clicks.count() > 0:
        mm_linkid   = get_xlmm_linkid(mm_clicks)
        xiaolu_mmset = XiaoluMama.objects.filter(id=mm_linkid)
        if xiaolu_mmset.count() > 0:
            xiaolu_mm = xiaolu_mmset[0]
            #计算小鹿妈妈订单返利
            mm_rebeta_amount    = xiaolu_mm.get_Mama_Trade_Amount(obj) 
            mm_order_rebeta     = xiaolu_mm.get_Mama_Trade_Rebeta(obj)
            tongjiorder,state = StatisticsShopping.objects.get_or_create(linkid=mm_linkid,
                                                                   wxorderid=order_id)
            tongjiorder.linkname    = xiaolu_mm.weikefu
            tongjiorder.openid      = xd_openid
            tongjiorder.wxordernick = order_buyer_nick
            tongjiorder.wxorderamount = mm_order_amount
            tongjiorder.rebetamount   = mm_rebeta_amount
            tongjiorder.shoptime      = ordertime
            tongjiorder.tichengcount  = mm_order_rebeta
            tongjiorder.save()
            
            daytongji,state = StatisticsShoppingByDay.objects.get_or_create(linkid=mm_linkid,
                                                      tongjidate=target_time)
            daytongji.linkname   = xiaolu_mm.weikefu
            daytongji.ordernumcount    = F('ordernumcount') + 1
            daytongji.orderamountcount = F('orderamountcount') + mm_order_amount
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
                               wxordernick=order_buyer_nick,
                               wxorderamount=mm_order_amount,
                               shoptime=ordertime, 
                               tichengcount=mm_order_rebeta).save()
 
    else:
        tongjiorder,state = StatisticsShopping.objects.get_or_create(linkid=0, wxorderid=order_id)
        tongjiorder.openid = xd_openid
        tongjiorder.wxordernick=order_buyer_nick
        tongjiorder.wxorderamount = mm_order_amount
        tongjiorder.shoptime = ordertime
        tongjiorder.tichengcount=mm_order_rebeta
        tongjiorder.save()
    
signal_saletrade_pay_confirm.connect(tongji_saleorder, sender=SaleTrade)

from flashsale.pay.models_refund import SaleRefund
from flashsale.pay.signals import signal_saletrade_refund_confirm


def get_strade_wxid_iter(strade):
    
    buyer_openid = strade.get_buyer_openid()
    ordertime    = strade.pay_time
    wx_unionid = get_Unionid(buyer_openid,settings.WXPAY_APPID)
    if not wx_unionid:
        wx_unionid = strade.receiver_mobile or str(strade.buyer_id)
    xd_unoins  = WeixinUnionID.objects.filter(unionid=wx_unionid,app_key=settings.WEIXIN_APPID) #小店openid
    xd_openid  = wx_unionid
    if xd_unoins.count() > 0:
        xd_openid = xd_unoins[0].openid
    
    isinxiaolumms = XiaoluMama.objects.filter(openid=wx_unionid,
                                             charge_status=XiaoluMama.CHARGED,
                                             charge_time__lte=ordertime)
    if isinxiaolumms.count() > 0:
        return isinxiaolumms[0], xd_openid, wx_unionid
    return None, xd_openid, wx_unionid

def refund_rebeta_takeoff(sender, obj, **kwargs):
    """ 退款取消或扣除订单提成 """
    sorder = SaleOrder.objects.get(id=obj.order_id)
    strade = sorder.sale_trade
    #押金，充值,钱包支付没有提成
    if strade.is_Deposite_Order() or strade.channel == SaleTrade.WALLET:
        return 
    
    order_id          = strade.tid
    order_time        = strade.pay_time
    today       = datetime.date.today()
    target_date = order_time.date()
    if target_date > today:
        target_date = today

    xlmm, openid, unionid = get_strade_wxid_iter(strade)
    if not xlmm:
        return 
    
    shoppings = StatisticsShopping.objects.filter(wxorderid=order_id)\
        .exclude(status=StatisticsShopping.REFUNDED)
    if shoppings.count() == 0:
        return
    shopping  = shoppings[0]
    daytongji,state = StatisticsShoppingByDay.objects.get_or_create(linkid=xlmm.id,
                                                      tongjidate=order_time.date())
    
    #订单返利是否结算
    is_balanced = shopping.is_balanced()
    mm_rebeta_amount    = xlmm.get_Mama_Trade_Amount(strade) 
    mm_order_rebeta     = xlmm.get_Mama_Trade_Rebeta(strade)
    
    delta_amount  = shopping.rebetamount  - mm_rebeta_amount
    delta_rebeta  = shopping.tichengcount - mm_order_rebeta
    shopping_status = shopping.status
    if mm_rebeta_amount == 0 :
        shopping_status = StatisticsShopping.REFUNDED 
        
    if is_balanced:
        clog,state = CarryLog.objects.get_or_create(
            xlmm=xlmm.id,
            order_num=obj.id,
            log_type=CarryLog.REFUND_OFF
        )
        if not state and clog.status != CarryLog.PENDING:
            return
        delta_rebeta = (obj.refund_fee / strade.payment) * shopping.tichengcount
        clog.buyer_nick=xlmm.weikefu
        clog.value=delta_rebeta
        clog.carry_type=CarryLog.CARRY_OUT
        clog.status=CarryLog.PENDING
        clog.carry_date=obj.modified
        clog.save()
    else:
        shopping.rebetamount  = delta_amount 
        shopping.tichengcount = delta_rebeta
        shopping.status = shopping_status
        shopping.save()
    
    

signal_saletrade_refund_confirm.connect(refund_rebeta_takeoff, sender=SaleRefund)
