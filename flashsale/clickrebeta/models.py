# -*- coding:utf-8 -*-
import datetime
from django.db import models
from django.db.models.signals import post_save
from shopapp.weixin.models import WXOrder
from flashsale.clickcount.models import Clicks
from flashsale.xiaolumm.models import XiaoluMama, AgencyLevel, CarryLog
from django.db.models import Sum

CLICK_VALID_DAYS = 2


class NormalShopingManager(models.Manager):
    def get_queryset(self):
        super_tm = super(NormalShopingManager, self)
        return super_tm.get_queryset().filter(status__in=self.model.NORMAL_STATUS)


class StatisticsShopping(models.Model):
    WAIT_SEND = 0
    FINISHED = 1
    REFUNDED = 2

    SHOPPING_STATUS = (
        (WAIT_SEND, u'已付款'),
        (FINISHED, u'已完成'),
        (REFUNDED, u'已取消'),
    )

    NORMAL_STATUS = [WAIT_SEND, FINISHED]

    linkid = models.IntegerField(default=0, verbose_name=u"妈妈ID")
    linkname = models.CharField(max_length=20, default="", verbose_name=u'代理人')
    openid = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u"收货手机")
    wxorderid = models.CharField(max_length=64, db_index=True, verbose_name=u'微信订单')
    wxordernick = models.CharField(max_length=32, verbose_name=u'购买昵称')
    wxorderamount = models.IntegerField(default=0, verbose_name=u'微信订单价格')
    rebetamount = models.IntegerField(default=0, verbose_name=u'有效金额')
    tichengcount = models.IntegerField(default=0, verbose_name=u'订单提成')
    shoptime = models.DateTimeField(default=datetime.datetime.now, db_index=True, verbose_name=u'提成时间')
    status = models.IntegerField(default=WAIT_SEND, db_index=True, choices=SHOPPING_STATUS, verbose_name=u'订单状态')

    objects = models.Manager()
    normal_objects = NormalShopingManager()

    class Meta:
        db_table = 'flashsale_tongji_shopping'
        unique_together = ('linkid', 'wxorderid')
        app_label = 'clickrebeta'
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

    def normal_orders(self):
        return self.detail_orders.filter(
            status__in=(
                OrderDetailRebeta.WAIT_SEND,
                OrderDetailRebeta.FINISHED
            )
        )

    def is_balanced(self):
        clogs = CarryLog.objects.filter(xlmm=self.linkid,
                                        log_type=CarryLog.ORDER_REBETA,
                                        carry_date=self.shoptime.date())
        if clogs.count() == 0:
            return False
        clog = clogs[0]
        return clog.status != CarryLog.PENDING

    def pro_pic(self):
        """ 返回有提成订单的产品图片　"""
        from shopback.items.models import Product
        sod = SaleOrder.objects.filter(sale_trade__tid=self.wxorderid,  # 这里至返回没有退款的订单
                                       refund_status=SaleRefund.NO_REFUND).only('item_id')
        if sod.exists():  # 至返回第一个产品的图片
            pro = Product.objects.get(id=sod[0].item_id).pic_path
            return pro
        else:
            return None

    def day_time(self):
        return self.shoptime.strftime("%H:%M")

    def dayly_ticheng(self):
        """ 计算当天的提成总额 """
        df = self.shoptime.date()
        dt = df + datetime.timedelta(days=1)
        shops = self.__class__.objects.filter(linkid=self.linkid,
                                              shoptime__gte=df,
                                              shoptime__lt=dt).exclude(status=StatisticsShopping.REFUNDED)
        sum_value = shops.aggregate(sum_value=Sum('tichengcount')).get('sum_value') or 0
        return sum_value / 100.0


class OrderDetailRebeta(models.Model):
    """ 订单佣金明细 """
    WAIT_SEND = 0
    FINISHED = 1
    REFUNDED = 2

    SHOPPING_STATUS = (
        (WAIT_SEND, u'已付款'),
        (FINISHED, u'已完成'),
        (REFUNDED, u'已退款'),
    )

    order = models.ForeignKey(StatisticsShopping, null=True, related_name='detail_orders', verbose_name='订单')
    detail_id = models.CharField(max_length=64, db_index=True, verbose_name=u'订单明细ID')
    scheme_id = models.IntegerField(default=0, verbose_name=u'佣金计划ID')
    pay_time = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'支付时间')
    order_amount = models.IntegerField(default=0, verbose_name=u'支付金额')
    rebeta_amount = models.IntegerField(default=0, verbose_name=u'订单提成')
    status = models.IntegerField(default=WAIT_SEND, choices=SHOPPING_STATUS, verbose_name=u'订单状态')

    class Meta:
        db_table = 'flashsale_tongji_orderebeta'
        unique_together = ('order', 'detail_id')
        app_label = 'clickrebeta'
        verbose_name = u'订单佣金明细'
        verbose_name_plural = u'订单佣金明细'


def recalc_shopping_rebeta_amount(sender, instance, created, **kwargs):
    """ 重新计算订单提成，实付金额，以及提成状态 """
    if created:
        return

    shopping_order = instance.order
    total_amount = 0
    total_rebeta = 0
    order_status = 1
    for order in shopping_order.normal_orders():
        total_amount += order.order_amount
        total_rebeta += order.rebeta_amount
        order_status &= order.status

    shopping_order.rebetamount = total_amount
    shopping_order.tichengcount = total_rebeta
    shopping_order.status = order_status
    shopping_order.save()


post_save.connect(recalc_shopping_rebeta_amount, sender=OrderDetailRebeta)


class StatisticsShoppingByDay(models.Model):
    linkid = models.IntegerField(default=0, verbose_name=u"链接ID")
    linkname = models.CharField(max_length=20, default="", verbose_name=u'代理人')
    buyercount = models.IntegerField(default=0, verbose_name=u'购买人数')
    ordernumcount = models.IntegerField(default=0, verbose_name=u'订单总数')
    orderamountcount = models.IntegerField(default=0, verbose_name=u'订单总价')
    todayamountcount = models.IntegerField(default=0, verbose_name=u'提成总数')
    tongjidate = models.DateField(db_index=True, verbose_name=u'统计的日期')

    class Meta:
        db_table = 'flashsale_tongji_shopping_day'
        unique_together = ('linkid', 'tongjidate')
        app_label = 'clickrebeta'
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

def check_or_create_order_redenvelop(sender, instance, **kwargs):
    from flashsale.xiaolumm.tasks import order_Red_Packet_Pending_Carry
    # 首单十单红包创建 2015-07-08 添加
    order_Red_Packet_Pending_Carry(instance.linkid, datetime.date.today())


post_save.connect(check_or_create_order_redenvelop, sender=StatisticsShoppingByDay)


def update_statistic_shopping_stat(sender, instance, **kwargs):
    """ 具体的订单提成及状态变更，则触发更新妈妈日订单提成统计 """
    tongji_date = instance.shoptime.date()
    mm_linkid = instance.linkid
    day_shoppings = StatisticsShoppingByDay.objects.filter(tongjidate=tongji_date,
                                                           linkid=instance.linkid)
    if not day_shoppings.exists():
        return

    day_shopping = day_shoppings[0]
    stat_start = datetime.datetime(tongji_date.year, tongji_date.month, tongji_date.day)
    stat_end = datetime.datetime(tongji_date.year, tongji_date.month, tongji_date.day, 23, 59, 59)
    stat_shoppings = StatisticsShopping.objects.filter(linkid=mm_linkid,
                                                       status__in=(
                                                       StatisticsShopping.WAIT_SEND, StatisticsShopping.FINISHED),
                                                       shoptime__range=(stat_start, stat_end))
    shoppings_dict = stat_shoppings.aggregate(total_wxorderamount=models.Sum('wxorderamount'),
                                              total_tichengcount=models.Sum('tichengcount'))
    day_shopping.ordernumcount = stat_shoppings.count()
    day_shopping.buyercount = stat_shoppings.values('openid').distinct().count()
    day_shopping.orderamountcount = shoppings_dict.get('total_wxorderamount') or 0
    day_shopping.todayamountcount = shoppings_dict.get('total_tichengcount') or 0
    day_shopping.save()


post_save.connect(update_statistic_shopping_stat, sender=StatisticsShopping)


def get_xlmm_linkid(click_set):
    ''' 根据点击获取小鹿妈妈ID '''
    exclude_xlmmids = (0, 44)
    for cc in click_set:
        if cc.linkid in exclude_xlmmids:
            continue
        return cc.linkid
    return 44


from django.db.models import F
from django.conf import settings
from shopapp import signals
from shopapp.weixin.options import get_openid_by_unionid, get_unionid_by_openid


def tongji_wxorder(sender, obj, **kwargs):
    """ 统计微信小店订单订单提成信息 """

    today = datetime.date.today()
    target_time = obj.order_create_time.date()
    if target_time > today:
        target_time = today

    ordertime = obj.order_create_time
    order_stat_from = ordertime - datetime.timedelta(days=CLICK_VALID_DAYS)
    mm_order_amount = obj.order_total_price
    mm_rebeta_amount = 0
    mm_order_rebeta = 0
    buyer_mobile = obj.receiver_mobile
    wx_unionid = get_unionid_by_openid(obj.buyer_openid, settings.WEIXIN_APPID)
    isinxiaolumm = XiaoluMama.objects.filter(openid=wx_unionid,
                                             charge_status=XiaoluMama.CHARGED,
                                             charge_time__lte=ordertime)

    if isinxiaolumm.count() > 0:
        xiaolumm = isinxiaolumm[0]
        # 计算小鹿妈妈订单返利
        mm_rebeta_amount = xiaolumm.get_Mama_Trade_Amount(obj)
        mm_order_rebeta = xiaolumm.get_Mama_Trade_Rebeta(obj)
        tongjiorder, state = StatisticsShopping.objects.get_or_create(linkid=xiaolumm.id,
                                                                      wxorderid=str(obj.order_id))
        tongjiorder.linkname = xiaolumm.weikefu
        tongjiorder.openid = buyer_mobile
        tongjiorder.wxordernick = obj.buyer_nick
        tongjiorder.wxorderamount = mm_order_amount
        tongjiorder.rebetamount = mm_rebeta_amount
        tongjiorder.shoptime = obj.order_create_time
        tongjiorder.tichengcount = mm_order_rebeta
        tongjiorder.save()

        daytongji, state = StatisticsShoppingByDay.objects.get_or_create(linkid=xiaolumm.id,
                                                                         tongjidate=target_time)
        if state:
            daytongji.buyercount = 1
            daytongji.linkname = xiaolumm.weikefu
            daytongji.ordernumcount = 1
            daytongji.orderamountcount = mm_order_amount
            daytongji.todayamountcount = mm_order_rebeta
            daytongji.save()
        return

    mm_clicks = Clicks.objects.filter(click_time__range=(order_stat_from, ordertime)).filter(
        openid=obj.buyer_openid).order_by('-click_time')
    if mm_clicks.count() > 0:
        mm_linkid = get_xlmm_linkid(mm_clicks)
        mm_order_rebeta = obj.order_total_price

        xiaolu_mmset = XiaoluMama.objects.filter(id=mm_linkid)
        if xiaolu_mmset.count() > 0:
            xiaolu_mm = xiaolu_mmset[0]
            # 计算小鹿妈妈订单返利
            mm_rebeta_amount = xiaolu_mm.get_Mama_Trade_Amount(obj)
            mm_order_rebeta = xiaolu_mm.get_Mama_Trade_Rebeta(obj)
            tongjiorder, state = StatisticsShopping.objects.get_or_create(linkid=mm_linkid,
                                                                          wxorderid=str(obj.order_id))
            tongjiorder.linkname = xiaolu_mm.weikefu
            tongjiorder.openid = buyer_mobile
            tongjiorder.wxordernick = obj.buyer_nick
            tongjiorder.wxorderamount = mm_order_amount
            tongjiorder.rebetamount = mm_rebeta_amount
            tongjiorder.shoptime = obj.order_create_time
            tongjiorder.tichengcount = mm_order_rebeta
            tongjiorder.save()

            daytongji, state = StatisticsShoppingByDay.objects.get_or_create(linkid=mm_linkid,
                                                                             tongjidate=target_time)
            if state:
                daytongji.buyercount = 1
                daytongji.linkname = xiaolu_mm.weikefu
                daytongji.ordernumcount = 1
                daytongji.orderamountcount = mm_order_amount
                daytongji.todayamountcount = mm_order_rebeta
                daytongji.save()

        else:
            StatisticsShopping(linkid=0,
                               openid=buyer_mobile,
                               wxorderid=str(obj.order_id),
                               wxorderamount=mm_order_amount,
                               shoptime=obj.order_create_time,
                               tichengcount=mm_order_rebeta).save()

    else:
        tongjiorder, state = StatisticsShopping.objects.get_or_create(linkid=0, wxorderid=str(obj.order_id))
        tongjiorder.openid = buyer_mobile
        tongjiorder.wxorderamount = mm_order_amount
        tongjiorder.shoptime = obj.order_create_time
        tongjiorder.tichengcount = mm_order_rebeta
        tongjiorder.save()


signals.signal_wxorder_pay_confirm.connect(tongji_wxorder, sender=WXOrder)

from flashsale.pay.models import SaleTrade, SaleOrder, Customer
from shopapp.weixin.models import WeixinUnionID
from flashsale.pay.signals import signal_saletrade_pay_confirm


def get_wxopenid(sale_trade, customer):
    wx_unionid = customer.unionid
    xd_openid = get_openid_by_unionid(wx_unionid, settings.WXPAY_APPID)
    return xd_openid, wx_unionid


def get_xiaolumm(sale_trade, customer):
    """ 获取小鹿妈妈 """
    obj = sale_trade
    ordertime = obj.pay_time
    order_stat_from = ordertime - datetime.timedelta(days=CLICK_VALID_DAYS)
    xd_openid, wx_unionid = get_wxopenid(sale_trade, customer)

    # 计算订单所属小鹿妈妈ID
    xiaolumms = XiaoluMama.objects.filter(openid=wx_unionid,
                                          charge_status=XiaoluMama.CHARGED)
    if xiaolumms.exists():
        return xiaolumms[0]

    xiaolumm = XiaoluMama.objects.get_by_saletrade(sale_trade)
    if xiaolumm:
        return xiaolumm

    if xd_openid:
        mm_clicks = Clicks.objects.filter(click_time__range=(order_stat_from, ordertime)).filter(
            openid=xd_openid).order_by('-click_time')  # 去掉0，44对应的小鹿妈妈ID
        mm_linkid = get_xlmm_linkid(mm_clicks)
        xiaolu_mmset = XiaoluMama.objects.filter(id=mm_linkid)
        if xiaolu_mmset.exists():
            return xiaolu_mmset[0]

    return None


end_time = datetime.datetime(2016, 3, 23, 23, 59, 59)


def tongji_saleorder(sender, obj, **kwargs):
    """ 统计特卖订单提成 """
    # 如果订单试用钱包付款，或是押金订单则不处理
    if obj.is_Deposite_Order():
        return

    if obj.pay_time > end_time:
        return

    today = datetime.date.today()
    target_time = obj.pay_time.date()
    if target_time > today:
        target_time = today

    ordertime = obj.pay_time
    buyer_mobile = obj.receiver_mobile
    customer = Customer.objects.get(id=obj.buyer_id)

    mm_order_amount = int(obj.payment * 100)
    mm_order_rebeta = 0
    mm_rebeta_amount = 0
    order_id = obj.tid
    order_buyer_nick = obj.buyer_nick or '%s(%s)' % (
        obj.receiver_name[0:24],
        obj.receiver_mobile[8:11]
    )

    xiaolu_mm = customer.get_referal_xlmm()
    if not xiaolu_mm:
        xiaolu_mm = get_xiaolumm(obj, customer)
    mm_linkid = xiaolu_mm and xiaolu_mm.id or 0

    if xiaolu_mm:
        # 计算小鹿妈妈订单返利
        mm_rebeta_amount = xiaolu_mm.get_Mama_Trade_Amount(obj)
        mm_order_rebeta = xiaolu_mm.get_Mama_Trade_Rebeta(obj)
        tongjiorder, state = StatisticsShopping.objects.get_or_create(linkid=mm_linkid,
                                                                      wxorderid=order_id)

        tongjiorder.linkname = xiaolu_mm.weikefu
        tongjiorder.openid = buyer_mobile
        tongjiorder.wxordernick = order_buyer_nick
        tongjiorder.wxorderamount = mm_order_amount
        tongjiorder.rebetamount = mm_rebeta_amount
        tongjiorder.shoptime = ordertime
        tongjiorder.tichengcount = mm_order_rebeta
        tongjiorder.save()

        daytongji, state = StatisticsShoppingByDay.objects.get_or_create(linkid=mm_linkid,
                                                                         tongjidate=target_time)
        if state:
            daytongji.buyercount = 1
            daytongji.linkname = xiaolu_mm.weikefu
            daytongji.ordernumcount = 1
            daytongji.orderamountcount = mm_order_amount
            daytongji.todayamountcount = mm_order_rebeta
            daytongji.save()
    else:
        StatisticsShopping(linkid=0,
                           openid=buyer_mobile,
                           wxorderid=order_id,
                           wxordernick=order_buyer_nick,
                           wxorderamount=mm_order_amount,
                           shoptime=ordertime,
                           tichengcount=mm_order_rebeta).save()


signal_saletrade_pay_confirm.connect(tongji_saleorder, sender=SaleTrade)

from flashsale.pay.models import SaleRefund
from flashsale.pay.signals import signal_saletrade_refund_confirm


def get_strade_wxid_iter(strade):
    """ 获取特卖订单微信openid,unionid """
    buyer_openid = strade.get_buyer_openid()
    ordertime = strade.pay_time
    wx_unionid = get_unionid_by_openid(buyer_openid, settings.WXPAY_APPID)
    if not wx_unionid:
        wx_unionid = strade.receiver_mobile or str(strade.buyer_id)
    xd_unoins = WeixinUnionID.objects.filter(unionid=wx_unionid, app_key=settings.WEIXIN_APPID)  # 小店openid
    xd_openid = wx_unionid
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
    # 押金，充值,钱包支付没有提成
    if strade.is_Deposite_Order() or strade.channel == SaleTrade.WALLET:
        return

    order_tid = strade.tid
    order_oid = sorder.oid
    order_time = strade.pay_time
    today = datetime.date.today()
    target_date = order_time.date()
    if target_date > today:
        target_date = today

    xlmm, openid, unionid = get_strade_wxid_iter(strade)
    if not xlmm:
        return

    shoppings = StatisticsShopping.objects.filter(wxorderid=order_tid)
    if not shoppings.exists() or shoppings[0].status == StatisticsShopping.REFUNDED:
        return
    shopping = shoppings[0]

    # 订单返利是否结算
    is_balanced = shopping.is_balanced()
    # 获取订单佣金明细
    detail_orders = OrderDetailRebeta.objects.filter(order=shopping, detail_id=order_oid)
    if detail_orders.exists():
        detail_order = detail_orders[0]
        detail_order.rebeta_amount = min((sorder.num - obj.refund_num) / sorder.num, 1) * detail_order.rebeta_amount
        detail_order.status = OrderDetailRebeta.REFUNDED
        detail_order.save()

        mm_rebeta_amount = detail_order.order.rebetamount
        mm_order_rebeta = detail_order.order.tichengcount
        delta_rebeta = (obj.refund_num / sorder.num) * detail_order.rebeta_amount
    else:
        mm_rebeta_amount = xlmm.get_Mama_Trade_Amount(strade)
        mm_order_rebeta = xlmm.get_Mama_Trade_Rebeta(strade)
        delta_rebeta = max(shopping.tichengcount - mm_order_rebeta, 0)

    shopping_status = shopping.status
    if mm_rebeta_amount == 0:
        shopping_status = StatisticsShopping.REFUNDED

    if is_balanced:
        clog, state = CarryLog.objects.get_or_create(
            xlmm=xlmm.id,
            order_num=obj.id,
            log_type=CarryLog.REFUND_OFF
        )
        if not state and clog.status != CarryLog.PENDING:
            return
        delta_rebeta = (obj.refund_fee / strade.payment) * shopping.tichengcount
        clog.buyer_nick = xlmm.weikefu
        clog.value = delta_rebeta
        clog.carry_type = CarryLog.CARRY_OUT
        clog.status = CarryLog.PENDING
        clog.carry_date = obj.modified
        clog.save()
    else:
        shopping.rebetamount = mm_rebeta_amount
        shopping.tichengcount = mm_order_rebeta
        shopping.status = shopping_status
        shopping.save()

        daytongji, state = StatisticsShoppingByDay.objects.get_or_create(linkid=xlmm.id,
                                                                         tongjidate=order_time.date())
        daytongji.todayamountcount = F('todayamountcount') - delta_rebeta
        daytongji.save()

        CarryLog.objects.filter(
            xlmm=xlmm.id,
            order_num=strade.pay_time.strftime('%y%m%d'),
            log_type=CarryLog.ORDER_REBETA
        ).update(value=F('value') + delta_rebeta)


signal_saletrade_refund_confirm.connect(refund_rebeta_takeoff, sender=SaleRefund)
