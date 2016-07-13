# -*- coding: utf-8 -*-
import datetime
from .models import MergeTrade, MergeOrder
from shopback.base.service import LocalService
from shopback.orders.service import OrderService
from shopback.fenxiao.service import PurchaseOrderService
from shopapp.weixin.service import WxShopService
from shopapp.jingdong.service import JDShopService
from flashsale.pay.services import FlashSaleService
from shopback import paramconfig as pcfg
from common.utils import update_model_fields


class LocalTradeService():
    def __init__(self, t):

        if isinstance(t, MergeTrade):
            self.trade = t
        else:
            self.trade = MergeTrade.objects.get(
                type__in=(MergeTrade.YHD_TYPE,
                          MergeTrade.DD_TYPE,
                          MergeTrade.SN_TYPE,
                          MergeTrade.DIRECT_TYPE,
                          MergeTrade.REISSUE_TYPE,
                          MergeTrade.EXCHANGE_TYPE),
                tid=t)

    @classmethod
    def createTrade(cls, user_id, tid, *args, **kwargs):
        """ TODO """
        pass

    @classmethod
    def createMergeTrade(cls, trade, *args, **kwargs):
        """ TODO """
        pass

    def payTrade(self, *args, **kwargs):
        """ TODO """
        pass

    def sendTrade(self, *args, **kwargs):

        self.trade.status = pcfg.WAIT_BUYER_CONFIRM_GOODS
        self.trade.consign_time = datetime.datetime.now()
        self.trade.save()


TRADE_TYPE_SERVICE_MAP = {
    pcfg.FENXIAO_TYPE: PurchaseOrderService,
    pcfg.TAOBAO_TYPE: OrderService,
    pcfg.SALE_TYPE: FlashSaleService,
    pcfg.GUARANTEE_TYPE: OrderService,
    pcfg.TB_STEP_TYPE: OrderService,
    pcfg.COD_TYPE: OrderService,
    pcfg.JD_TYPE: JDShopService,
    pcfg.YHD_TYPE: LocalTradeService,
    pcfg.DD_TYPE: LocalTradeService,
    pcfg.WX_TYPE: WxShopService,
    pcfg.AMZ_TYPE: LocalService,
    pcfg.DIRECT_TYPE: LocalTradeService,
    pcfg.EXCHANGE_TYPE: LocalTradeService,
    pcfg.REISSUE_TYPE: LocalTradeService,
}


class TradeService(LocalService):
    trade = None
    bservice = None

    def __init__(self, user_id, t):
        assert t not in ('', None)

        if isinstance(t, MergeTrade):
            self.trade = t
        else:
            self.trade = MergeTrade.objects.get(
                user__visitor_id=user_id,
                tid=t)

        self.bservice = self.getBaseService()

    def getBaseService(self):
        origin_tid = self.trade.tid.split('-')[0]
        return TRADE_TYPE_SERVICE_MAP.get(self.trade.type, LocalService)(origin_tid)

    @classmethod
    def isTradeExist(cls, user_id, tid):
        try:
            MergeTrade.objects.get(user__visitor_id=user_id, tid=tid)
        except MergeTrade.DoesNotExist:
            return False
        return True

    @classmethod
    def getBaseServiceClass(cls, trade_type, *args, **kwargs):

        return TRADE_TYPE_SERVICE_MAP.get(trade_type, LocalService)

    @classmethod
    def createTrade(cls, user_id, tid, trade_type, *args, **kwargs):

        service_class = cls.getBaseServiceClass(trade_type)
        base_trade = service_class.createTrade(user_id, tid, *args, **kwargs)

        return service_class.createMergeTrade(base_trade)

    @classmethod
    def isValidPubTime(cls, userId, tradeId, msgTime):

        return MergeTrade.objects.isValidPubTime(userId, tradeId, msgTime)

    @classmethod
    def updatePublicTime(cls, userId, tradeId, msgTime):

        return MergeTrade.objects.updatePubTime(userId, tradeId, msgTime)

    def payTrade(self, *args, **kwargs):

        self.merge_trade = self.bservice.payTrade(*args, **kwargs)

    def sendTrade(self, *args, **kwargs):

        company_code = ''
        if self.trade.logistics_company:
            company_code = self.trade.logistics_company.code

        return self.bservice.sendTrade(company_code=company_code,
                                       out_sid=self.trade.out_sid,
                                       is_cod=self.trade.is_cod,
                                       serial_no=self.trade.id,
                                       merge_trade=self.trade)

    def ShipTrade(self, oid, *args, **kwargs):

        self.bservice.shipTrade(oid, *args, **kwargs)

        self.trade.merge_orders.filter(oid=oid) \
            .update(status=pcfg.WAIT_BUYER_CONFIRM_GOODS)

        if self.trade.merge_orders.filter(
                sys_status=pcfg.IN_EFFECT,
                gift_type=pcfg.REAL_ORDER_GIT_TYPE,
                status=pcfg.WAIT_SELLER_SEND_GOODS).count() > 0:
            return

        self.trade.merge_orders.filter(sys_status=pcfg.IN_EFFECT) \
            .update(status=pcfg.WAIT_BUYER_CONFIRM_GOODS)

        self.trade.status = pcfg.WAIT_BUYER_CONFIRM_GOODS
        self.trade.consign_time = datetime.datetime.now()

        update_model_fields(self.trade, update_fields=['status', 'consign_time'])

    def finishTrade(self, oid, *args, **kwargs):
        pass

    def closeTrade(self, oid, *args, **kwargs):

        self.changeTrade()

    def memoTrade(self, *args, **kwargs):

        self.changeTrade()

    def changeTrade(self, *args, **kwargs):

        if self.trade.status in (pcfg.TRADE_NO_CREATE_PAY,
                                 pcfg.WAIT_BUYER_PAY,
                                 pcfg.TRADE_CLOSED_BY_TAOBAO):
            TradeService.createTrade(
                self.trade.user.visitor_id,
                self.trade.tid,
                self.trade.type)
        else:
            self.payTrade(*args, **kwargs)

    def changeTradeOrder(self, oid, *args, **kwargs):
        self.changeTrade()

    def remindTrade(self, *args, **kwargs):

        self.trade.priority = pcfg.PRIORITY_HIG
        update_model_fields(self.trade, update_fields=['priority'])
