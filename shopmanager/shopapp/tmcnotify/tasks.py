#-*- coding:utf8 -*-
import re
import json
from celery.task import task
from celery.task.sets import subtask
from celery import Task
from shopback.users import Seller
from shopback.trades.service import TradeService
from django.conf import settings
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
        
        if not TradeService.isTradeExist(tradeId):
            TradeService.createTrade(UserId,tradeId,tradeType)
        
        if not TradeService.isValidPubTime(tradeId,msgTime):
            return
        
        if msgCode   == 'TradeCloseAndModifyDetailOrder':
            pass
        elif msgCode == 'TradeClose':    
            pass
        elif msgCode == 'TradeBuyerPay':  
            TradeService(tradeId).payTrade()
        elif msgCode == 'TradeSellerShip':  
            pass
        elif msgCode == 'TradePartlyRefund':  
            pass
        elif msgCode == 'TradeSuccess':  
            pass
        elif msgCode == 'TradeTimeoutRemind':  
            pass
        elif msgCode == 'TradeMemoModified':
            pass
        elif msgCode == 'TradeChanged': 
            pass
        elif msgCode == 'TradeAlipayCreate':    
            pass
               
    
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
        
    def run(self,message):
        
#        try:

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
            
        return (self.getMessageId(message),True)
    
#        except Exception,exc:
#            logger.error(exc.message,exc_info=True)
#            return (self.getMessageId(message),False)
                
    
class ProcessMessageCallBack(Task):
    """ 处理消息回调"""
    
    def run(self,message_status):
        
        try:
            pass
        except:
            pass    
        
    
