#-*- coding:utf8 -*-
import re
import json
from celery.task import task
from celery.task.sets import subtask
from celery import Task
from shopapp.tmcnotify.models import TmcUser
from shopback.users import Seller
from shopback.trades.service import TradeService
from django.conf import settings
from auth import apis
from common.utils import parse_datetime


class ProcessMessageTask(Task):
    """ 处理消息 """
    
    
    def getMessageType(self,message):
        return message['topic']
        
    def getMessageBody(self,message):
        return json.loads(message['content'])
    
    def getMessageId(self,message):
        return message['id']
    
    def getMessageTime(self,message):
        return parse_datetime(message['pub_time'])
    
    def handleTradeMessage(self,userId,msgCode,content,msgTime):
        
        tradeType  = content.get('type')
        tradeId    = content.get('tid')
        
        if (not TradeService.isTradeExist(tradeId) or 
            msgCode == 'TradeAlipayCreate'):
            
            TradeService.createTrade(UserId,tradeId,tradeType)
        
        if not TradeService.isValidPubTime(tradeId,msgTime):
            return
        
        t_service = TradeService(tradeId)
        if msgCode in ('TradeClose' 'TradeCloseAndModifyDetailOrder'):    
            t_service.closeTrade()
        elif msgCode == 'TradeBuyerPay':  
            t_service.payTrade()
        elif msgCode == 'TradeSellerShip':  
            t_service.shipTrade()
        elif msgCode == 'TradePartlyRefund':  
            t_service.sendTrade()
        elif msgCode == 'TradeSuccess':  
            t_service.finishTrade()
        elif msgCode == 'TradeTimeoutRemind':  
            t_service.remindTrade()
        elif msgCode == 'TradeMemoModified':
            t_service.memoTrade()
        elif msgCode == 'TradeChanged': 
            t_service.changeTrade()
               
    
    def handleRefundMessage(self,userId,msgCode,content,msgTime):
        
        pass
    
    def handleItemMessage(self,userId,msgCode,content,msgTime):
        
        pass
    
    def getTradeMessageCode(self,msgType):
        
        reg = re.compile('^taobao_trade_(?P<msgCode>\w+)$')
        m   = reg.match(msgType)
        return m and m.groupdict().get('msgCode')
        
    def getRefundMessageCode(self,msgType):
        
        reg = re.compile('^taobao_refund_(?P<msgCode>\w+)$')
        m   = reg.match(msgType)
        return m and m.groupdict().get('msgCode')
    
    def getItemMessageCode(self,msgType):
        
        reg = re.compile('^taobao_item_(?P<msgCode>\w+)$')
        m   = reg.match(msgType)
        
        return m and m.groupdict().get('msgCode')
        
    def getUserGroupName(self,user_id):
            
        return TmcUser.objects.get(user_id=user_id).group_name
    
    def successConsumeMessage(self,message):
        
        group_name = self.getUserGroupName(message['user_id'])
        apis.taobao_tmc_messages_confirm(group_name=group_name,
                                         s_message_ids='%d'%message.id,
                                         f_message_ids=None,
                                         tb_user_id=message['user_id'])
        
    def failConsumeMessage(self,message):
        
        group_name = self.getUserGroupName(message['user_id'])
        apis.taobao_tmc_messages_confirm(group_name=group_name,
                                         s_message_ids=None,
                                         f_message_ids='%d'%message.id,
                                         tb_user_id=message['user_id'])
    
    def run(self,message):
        
        try:
            msgType = self.getMessageType(message)
            content = self.getMessageBody(message)
            msgTime = self.getMessageTime(message)
            
            msgCode = self.getTradeMessageCode(msgType)
            if msgCode:
                self.handleTradeMessage( userId, msgCode, content, msgTime)
                
            msgCode = self.getRefundMessageCode(msgType)    
            if msgCode:
                self.handleRefundMessage( userId, msgCode, content, msgTime)
                
            msgCode = self.getItemMessageCode(msgType)    
            if msgCode:
                self.handleItemMessage( userId, msgCode, content, msgTime)
            
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
            self.failConsumeMessage(message)

        else:
            self.successConsumeMessage(message)
                
    
 
        
    
