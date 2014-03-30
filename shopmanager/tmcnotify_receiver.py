#-*- coding:utf8 -*-
import sys
import time
import datetime
import json
import urllib
import pycurl

from django.core.management import setup_environ
import settings
setup_environ(settings)

from shopapp.tmcnotify.models import TmcMessage,TmcUser,DEFAULT_GROUP_NAME
from shopapp.tmcnotify.tasks import ProcessMessageTask,ProcessMessageCallBack
from auth import apis
import logging

logger = logging.getLogger('notifyserver.handler')

CONSUME_MAX_RECODES = 200

class EmptyMessage(Exception):
    #for memo empty exception
    def __init__(self,msg=''):
        self.msg  = msg
    
    def __str__(self):
        return self.msg

class NotifyCommand():
    c    = None
    group_name = None
    user = None
    messageProcessor = ProcessMessageTask()
    messageCallBack  = ProcessMessageCallBack()
    
    def __init__(self,group_name=DEFAULT_GROUP_NAME):
        
        self.group_name = group_name
        self.user       = self.getPrimaryUser(group_name)
    
    def handle_daemon(self, *args, **options):
        
        if not self.user:
            return 
        
        while 1:

            try:
                self.consume_message(user=self.user)
            except EmptyMessage:
                #没有可用消息是休眠1分钟
                time.sleep(60) 
            except Exception,exc:
                logger.error(exc.message,exc_info=True)
                #休眠5分钟
                time.sleep(60*5)
    
    def getPrimaryUser(self,group_name):
        
        users = TmcUser.valid_users.filter(group_name=group_name)
        if users.count() == 0:
            return None
        
        try:
            return users.get(is_primary=True)
        except:
            return users[0]
        
        
    def getTotalResults(self,reponse):
        
        return response['tmc_messages_consume_response'].get('total_results')
        
    def getMessageFromResp(self,response):
        
        if not response['tmc_messages_consume_response'].get('messages'):
            raise EmptyMessage(u'暂没有的消息可消费')
        return response['tmc_messages_consume_response']['messages']['tmc_message']     
        
    def consume_message(self):
        
        response = apis.taobao_tmc_messages_consume(
                                                    group_name=self.group_name,
                                                    quantity=CONSUME_MAX_RECODES,
                                                    tb_user_id=self.user.user_id)
        
        message  = self.getMessageFromResp(response)
        self.handle_message(messages)
        
        
    def handle_message(self,messages):
        
        if settings.DEBUG:
            for m in messages:
                print self.messageProcessor(m)
        else:
            chord([self.messageProcessor.s(m) for m in messages])(self.messageCallBack.s())
    
        
if __name__ == '__main__':
    
    
    ms = [{u'content': u'{"buyer_nick":"\u6211\u7684\u6dd8\u6211\u7684\u5b9d22","payment":"30.36","oid":586070597376760,"tid":586070597376760,"type":"guarantee_trade","seller_nick":"\u4f18\u5c3c\u4e16\u754c\u65d7\u8230\u5e97"}', u'pub_time': u'2014-03-26 10:41:41', u'user_id': 174265168, u'pub_app_key': u'12497914', u'user_nick': u'\u4f18\u5c3c\u4e16\u754c\u65d7\u8230\u5e97', u'topic': u'taobao_trade_TradeBuyerPay', u'id': 6142200092063758446L}, 
          {u'content': u'{"buyer_nick":"damingfly","payment":"48.90","oid":585608839663430,"tid":585608839663430,"type":"guarantee_trade","seller_nick":"\u4f18\u5c3c\u4e16\u754c\u65d7\u8230\u5e97"}', u'pub_time': u'2014-03-25 21:59:21', u'user_id': 174265168, u'pub_app_key': u'12497914', u'user_nick': u'\u4f18\u5c3c\u4e16\u754c\u65d7\u8230\u5e97', u'topic': u'taobao_trade_TradeBuyerPay', u'id': 6142200092063758447L}, 
          {u'content': u'{"buyer_nick":"shanweida","payment":"111.46","oid":586004403606066,"tid":586004403606066,"type":"guarantee_trade","seller_nick":"\u4f18\u5c3c\u4e16\u754c\u65d7\u8230\u5e97"}', u'pub_time': u'2014-03-25 22:01:58', u'user_id': 174265168, u'pub_app_key': u'12497914', u'user_nick': u'\u4f18\u5c3c\u4e16\u754c\u65d7\u8230\u5e97', u'topic': u'taobao_trade_TradeBuyerPay', u'id': 6142200092063758448L}]
    c = NotifyCommand()
    c.handle_message(ms)
        
