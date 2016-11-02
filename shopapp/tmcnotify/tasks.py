# -*- coding:utf8 -*-
import re
import json
from django.conf import settings
from celery.task import task
from celery.task.sets import subtask
from celery import Task

from shopapp.tmcnotify.models import TmcUser, TmcMessage
from shopback.users import Seller
from shopback.trades.service import TradeService, OrderService
from shopback import paramconfig as pcfg
from auth import apis
from common.utils import parse_datetime
import logging

logger = logging.getLogger('notifyserver.handler')


class ProcessMessageTask(Task):
    """ 处理消息 """

    def getMessageType(self, message):
        return message['topic']

    def getMessageBody(self, message):
        return json.loads(message['content'])

    def getMessageId(self, message):
        return message['id']

    def getUserId(self, message):
        return message['user_id']

    def getMessageTime(self, message):
        return parse_datetime(message['pub_time'])

    def handleTradeMessage(self, userId, msgCode, content, msgTime):

        tradeType = content.get('type')
        tradeId = content.get('tid')
        oid = content.get('oid', None)

        if tradeType not in (pcfg.TAOBAO_TYPE,
                             pcfg.FENXIAO_TYPE,
                             pcfg.GUARANTEE_TYPE,
                             pcfg.COD_TYPE,
                             pcfg.TB_STEP_TYPE):
            raise Exception(u'系统不支持该淘宝订单类型:%s' % tradeType)

        if (not TradeService.isTradeExist(userId, tradeId) or
                    msgCode == 'TradeAlipayCreate'):

            if msgCode == 'TradeBuyerPay' and tradeType != pcfg.FENXIAO_TYPE:

                trade_dict = OrderService.getTradeFullInfo(userId, tradeId)
                trade = OrderService.saveTradeByDict(userId, trade_dict)

                OrderService.createMergeTrade(trade)

            else:
                TradeService.createTrade(userId, tradeId, tradeType)

            if tradeType == pcfg.FENXIAO_TYPE:
                return

            TradeService.updatePublicTime(userId, tradeId, msgTime)
            return

        if (msgCode != 'TradeBuyerPay' and
                not TradeService.isValidPubTime(userId, tradeId, msgTime)):
            return

        t_service = TradeService(userId, tradeId)
        if msgCode in ('TradeClose' 'TradeCloseAndModifyDetailOrder'):
            t_service.closeTrade(oid)

        elif msgCode == 'TradeBuyerPay':
            t_service.payTrade()

        elif msgCode == 'TradeSellerShip':
            t_service.shipTrade(oid)

        elif msgCode == 'TradePartlyRefund':
            pass

        elif msgCode == 'TradeSuccess':
            t_service.finishTrade(oid)

        elif msgCode == 'TradeTimeoutRemind':
            t_service.remindTrade()

        elif msgCode == 'TradeMemoModified':
            t_service.memoTrade()

        elif msgCode == 'TradeChanged':
            t_service.changeTrade()

        TradeService.updatePublicTime(userId, tradeId, msgTime)

    def handleRefundMessage(self, userId, msgCode, content, msgTime):

        tradeType = content.get('type')
        tradeId = content.get('tid')
        oid = content.get('oid', None)

        if tradeType not in (pcfg.TAOBAO_TYPE,
                             pcfg.FENXIAO_TYPE,
                             pcfg.GUARANTEE_TYPE,
                             pcfg.COD_TYPE,
                             pcfg.TB_STEP_TYPE):
            raise Exception(u'系统不支持该淘宝订单类型:%s' % tradeType)

        if (not TradeService.isTradeExist(userId, tradeId) or
                    msgCode == 'TradeAlipayCreate'):

            TradeService.createTrade(userId, tradeId, tradeType)

            if tradeType == pcfg.FENXIAO_TYPE:
                return

            TradeService.updatePublicTime(userId, tradeId, msgTime)
            return

        if not TradeService.isValidPubTime(userId, tradeId, msgTime):
            return

        t_service = TradeService(userId, tradeId)
        if msgCode in ('TradeClose' 'TradeCloseAndModifyDetailOrder'):
            t_service.closeTrade(oid)

        elif msgCode == 'TradeBuyerPay':
            t_service.payTrade()

        elif msgCode == 'TradeSellerShip':
            t_service.shipTrade(oid)

        elif msgCode == 'TradePartlyRefund':
            pass

        elif msgCode == 'TradeSuccess':
            t_service.finishTrade(oid)

        elif msgCode == 'TradeTimeoutRemind':
            t_service.remindTrade()

        elif msgCode == 'TradeMemoModified':
            t_service.memoTrade()

        elif msgCode == 'TradeChanged':
            t_service.changeTrade()

        TradeService.updatePublicTime(userId, tradeId, msgTime)

    def handleItemMessage(self, userId, msgCode, content, msgTime):

        pass

    def getTradeMessageCode(self, msgType):

        reg = re.compile('^taobao_trade_(?P<msgCode>\w+)$')
        m = reg.match(msgType)
        return m and m.groupdict().get('msgCode')

    def getRefundMessageCode(self, msgType):

        reg = re.compile('^taobao_refund_(?P<msgCode>\w+)$')
        m = reg.match(msgType)
        return m and m.groupdict().get('msgCode')

    def getItemMessageCode(self, msgType):

        reg = re.compile('^taobao_item_(?P<msgCode>\w+)$')
        m = reg.match(msgType)

        return m and m.groupdict().get('msgCode')

    def getUserGroupName(self, user_id):

        return TmcUser.valid_users.get(user_id=user_id).group_name

    def successConsumeMessage(self, message):

        if settings.DEBUG:
            tmc_msg, state = TmcMessage.objects.get_or_create(
                id=self.getMessageId(message))
            tmc_msg.is_exec = True
            tmc_msg.save()

        group_name = self.getUserGroupName(message['user_id'])
        apis.taobao_tmc_messages_confirm(group_name=group_name,
                                         s_message_ids='%d' % self.getMessageId(message),
                                         f_message_ids=',',
                                         tb_user_id=self.getUserId(message))

    def failConsumeMessage(self, message):

        group_name = self.getUserGroupName(message['user_id'])
        apis.taobao_tmc_messages_confirm(group_name=group_name,
                                         s_message_ids=',',
                                         f_message_ids='%d' % self.getMessageId(message),
                                         tb_user_id=self.getUserId(message))

    def saveTmcMessage(self, message):

        tmc_msg, state = TmcMessage.objects.get_or_create(
            id=self.getMessageId(message),
            user_id=self.getUserId(message))

        for k, v in message.iteritems():
            hasattr(tmc_msg, k) and setattr(tmc_msg, k, type(v) == 'dict' and json.dump(v) or v)

        tmc_msg.save()

    def run(self, message):

        try:
            if settings.DEBUG:
                self.saveTmcMessage(message)

            msgType = self.getMessageType(message)
            content = self.getMessageBody(message)
            msgTime = self.getMessageTime(message)
            userId = self.getUserId(message)

            msgCode = self.getTradeMessageCode(msgType)
            if msgCode:
                self.handleTradeMessage(userId, msgCode, content, msgTime)

            msgCode = self.getRefundMessageCode(msgType)
            if msgCode:
                self.handleRefundMessage(userId, msgCode, content, msgTime)

            msgCode = self.getItemMessageCode(msgType)
            if msgCode:
                self.handleItemMessage(userId, msgCode, content, msgTime)

        except Exception, exc:
            logger.error(exc.message, exc_info=True)
            self.failConsumeMessage(message)

        else:
            self.successConsumeMessage(message)
