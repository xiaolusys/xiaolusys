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
        
        chord([ProcessMessageTask.s(m) for m in messages])(ProcessMessageCallBack.s())
    
        
if __name__ == '__main__':
    
    c = Command()
    c.handle_daemon()
        
