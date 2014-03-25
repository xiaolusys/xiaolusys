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

from shopapp.tmcnotify.models import TmcMessage,TmcUser
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

class Command():
    c = None
    fail_wait_time = 0
    
    def handle_daemon(self, *args, **options):
        
        users = TmcUser.valid_users.all()
        if users.count()==0:
            return 
        
        while 1:
            self.fail_wait_time = 1
            try:
                self.consume_message(user=user)
            except Exception,exc:
                #服务暂时不可用，休眠一分钟
                if hasattr(exc,'args') and exc.args[0] == 28:
                    time.sleep(1)
                else:
                    logger.error(exc.message or str(exc.args),exc_info=True)
                    time.sleep(60) 
            else:
                #服务端断开连接，则选择服务端返回的时间来休眠
                time.sleep(self.fail_wait_time or 5)
    
    def getMessageFromResp(self,response):
        
        if response.get('total_results') == 0:
            raise EmptyMessage(u'暂没有可消费的消息')
        return response['tmc_messages_consume_response']['messages']['tmc_message']     
        
    def consume_message(self,user=None):
        
        response = apis.taobao_tmc_messages_consume(
                                                    group_name=None,
                                                    quantity=CONSUME_MAX_RECODES,
                                                    tb_user_id=user.user_id)
        
        
        
        
    def handle_message(self,messages):
        #交易消息处理
        if item.has_key('notify_trade'):
            trade_dict = item['notify_trade']
            TradeNotify.save_and_post_notify(trade_dict)
            
        #商品消息处理
        if item.has_key('notify_item'):
            item_dict = item['notify_item']
            ItemNotify.save_and_post_notify(item_dict)

        #退款消息处理
        if item.has_key('notify_refund'):
            refund_dict = item['notify_refund']
            RefundNotify.save_and_post_notify(refund_dict)
    
        
if __name__ == '__main__':
    
    c = Command()
    c.handle_daemon()
        
