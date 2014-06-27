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
from celery import group

from shopapp.tmcnotify.models import TmcMessage,TmcUser,DEFAULT_GROUP_NAME
from shopapp.tmcnotify.tasks import ProcessMessageTask
from auth import apis
import logging

logger = logging.getLogger('notifyserver.handler')

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
    
    def __init__(self,group_name=DEFAULT_GROUP_NAME):
        
        self.group_name = group_name
        self.user       = self.getPrimaryUser(group_name)
    
    def handle_daemon(self, *args, **options):
        
        if not self.user:
            return 
        while 1:
            try:
                self.consume_message()
            except EmptyMessage:
                #没有可用消息是休眠30秒
                time.sleep(30) 
            except Exception,exc:
                logger.error(u'淘宝消息服务错误：%s'%exc.message,exc_info=True)
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
            raise EmptyMessage(u'暂没有消息可消费')
        return response['tmc_messages_consume_response']['messages']['tmc_message']     
        
    def consume_message(self):
        
        response = apis.taobao_tmc_messages_consume(
                                                    group_name=self.group_name,
                                                    quantity=self.user.quantity,
                                                    tb_user_id=self.user.user_id)
        
        messages  = self.getMessageFromResp(response)
        self.handle_message(messages)
        
        
    def handle_message(self,messages):
        
        if settings.DEBUG:
            for m in messages:
                print 'debug message:',m
                self.messageProcessor(m)
        else:
            group([self.messageProcessor.s(m) for m in messages]).apply_async()
    
        
if __name__ == '__main__':
    
    
    ms = [{u'content': u'{"buyer_nick":"\u6211\u7684\u6dd8\u6211\u7684\u5b9d22","payment":"30.36","oid":586070597376760,"tid":586070597376760,"type":"guarantee_trade","seller_nick":"\u4f18\u5c3c\u4e16\u754c\u65d7\u8230\u5e97"}', u'pub_time': u'2014-03-26 10:41:41', u'user_id': 174265168, u'pub_app_key': u'12497914', u'user_nick': u'\u4f18\u5c3c\u4e16\u754c\u65d7\u8230\u5e97', u'topic': u'taobao_trade_TradeBuyerPay', u'id': 6142200092063758446L}, 
          {u'content': u'{"buyer_nick":"damingfly","payment":"48.90","oid":585608839663430,"tid":585608839663430,"type":"guarantee_trade","seller_nick":"\u4f18\u5c3c\u4e16\u754c\u65d7\u8230\u5e97"}', u'pub_time': u'2014-03-25 21:59:21', u'user_id': 174265168, u'pub_app_key': u'12497914', u'user_nick': u'\u4f18\u5c3c\u4e16\u754c\u65d7\u8230\u5e97', u'topic': u'taobao_trade_TradeBuyerPay', u'id': 6142200092063758447L}, 
          {u'content': u'{"buyer_nick":"shanweida","payment":"111.46","oid":586004403606066,"tid":586004403606066,"type":"guarantee_trade","seller_nick":"\u4f18\u5c3c\u4e16\u754c\u65d7\u8230\u5e97"}', u'pub_time': u'2014-03-25 22:01:58', u'user_id': 174265168, u'pub_app_key': u'12497914', u'user_nick': u'\u4f18\u5c3c\u4e16\u754c\u65d7\u8230\u5e97', u'topic': u'taobao_trade_TradeBuyerPay', u'id': 6142200092063758448L}]
    
    if len(sys.argv) != 2:
        print >> sys.stderr, "usage: python *.py <group_name>"
    
    c = NotifyCommand(group_name=sys.argv[1])
    c.handle_daemon()
    #c.handle_message(ms)
        
