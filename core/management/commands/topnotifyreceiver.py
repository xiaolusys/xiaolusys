#-*- coding:utf8 -*-
import sys
import time
import datetime
import json
import urllib
import pycurl
from django.conf import settings
from daemonextension import DaemonCommand
from django.core.management import call_command
from shopback.users.models import User
from shopapp.notify.models import ItemNotify,TradeNotify,RefundNotify
from common.utils import getSignatureTaoBao
from shopapp.notify.tasks import  process_discard_notify_task
import logging

logger = logging.getLogger('notifyserver.handler')

CURL_READ_TIMEOUT    = 100
CURL_CONNECT_TIMEOUT = 60


class Command(DaemonCommand):
#class Command():
    c = None
    fail_wait_time = 0
    
    def handle_daemon(self, *args, **options):
        
        users = User.objects.all()
        if users.count()==0:
            return 
        
        while 1:
            self.fail_wait_time = 1
            try:
                self.notify()
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
            
    def get_curl(self):
        if self.c:
            return self.c
        self.c = pycurl.Curl()
        return self.c
        
    def notify(self,user=None):
        params = self.get_params(user=user)
        c = self.get_curl()
        c.setopt(pycurl.URL, settings.TAOBAO_NOTIFY_URL)
        c.setopt(pycurl.POSTFIELDS, urllib.urlencode(params))
        c.setopt(pycurl.WRITEFUNCTION,self.handle_body)
        c.setopt(pycurl.HEADERFUNCTION,self.handle_header)
        #c.setopt(pycurl.CONNECTTIMEOUT, CURL_CONNECT_TIMEOUT)
        c.setopt(pycurl.TIMEOUT, CURL_READ_TIMEOUT)
        c.setopt(pycurl.FAILONERROR,True)
        c.perform()
        
    def get_params(self,user=None):
        params = {}
        params['app_key'] = settings.APPKEY
        if user:
            params['user']    = user.visitor_id
        params['v']       = '2.0'
        params['format']  = 'json'
        params['sign_method']    = 'md5'
        params['timestamp'] = int(time.time())
        params['sign']    = getSignatureTaoBao(params,settings.APPSECRET)
        return params
    
    def handle_header(self,buf):
        print 'header:'+buf    
    
    def handle_body(self,buf):
        try:
            #print 'body:',buf
            if not buf.strip() :
                return 
            note  = json.loads(buf)
            code,msg = note['packet']['code'],note['packet'].get('msg',None)
            
            if code == 202:
                if not msg:
                    return 
                self.save_message(msg)
            elif code == 203:
                process_discard_notify_task.delay(msg['begin'],msg['end'])
            elif code in (101,102,103):
                self.fail_wait_time = msg or 10
            elif code == 105:
                self.fail_wait_time = 1
            elif code == 104:
                self.fail_wait_time = 0
        except Exception,exc:
            logger.info(exc.message.strip() or 'empty error')
        

    def save_message(self,item):
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
    
        
#if __name__ == '__main__':
    
#    c = Command()
#    c.handle_daemon()
        
