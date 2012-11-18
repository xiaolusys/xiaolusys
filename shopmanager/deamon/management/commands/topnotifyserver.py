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
from shopapp.notify.models import NotifyItem,NotifyTrade,NotifyRefund
from shopapp.notify.tasks import process_trade_notify_task,process_item_notify_task,process_refund_notify_task
import logging

logger = logging.getLogger('notifyserver.handler')

CURL_READ_TIMEOUT    = 10
CURL_CONNECT_TIMEOUT = 60

class Command(DaemonCommand):
    c = None
    fail_wait_time = 0
    
    def handle_daemon(self, *args, **options):

        users = User.obejcts.all()
        if users.count()==0:
            return 
        
        while 1:
            try:
                self.notify()
            except Exception,exc:
                #服务暂时不可用，休眠一分钟
                logger.error(exc.message,exc_info=True)
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
        c.setopt(pycurl.CONNECTTIMEOUT, CURL_CONNECT_TIMEOUT)
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
        
    def handle_body(self,buf):
        if not buf:
            return 
        note  = json.loads(buf)
        code,msg = note['packet']['code'],not['packet'].get('msg',None)
        
        if code == 202:
            if not msg:
                return 
            self.save_message(msg)
        elif code == 203:
            process_discard_notify_task.s(msg['begin'],msg['end'])
        elif code in (101,102,103):
            self.fail_wait_time = msg or 10
        elif code in (104,105):
            self.fail_wait_time = 10
            logger.warn(buf)
        

    def save_message(self,item):
        #交易消息处理
        if item.has_key('notify_trade'):
            trade_dict = item['notify_trade']
            trade_notify,state = NotifyTrade.objects.get_or_create(
                                                                   user_id=trade_dict['user_id'],
                                                                   tid=trade_dict['tid'],
                                                                   oid=trade_dict['oid'],
                                                                   status=trade_dict['status'],
                                                                   )
            trade_modified = datetime.dateime.strptime(trade_dict['modified'],'%Y-%m-%d %H:%M:%S')
            if state or trade_notify.modifid < trade_modified:
                for k,v in trade_dict.iteritems():
                    hasattr(trade_notify,k) and setattr(trade_notify,k,v)
                trade_notify.save()   
            process_trade_notify_task.s(trade_notify.id)
        #商品消息处理
        if item.has_key('notify_item'):
            item_dict = item['notify_item']
            item_notify,state = NotifyItem.objects.get_or_create(
                                                               user_id=item_dict['user_id'],
                                                               num_iid=item_dict['num_iid'],
                                                               sku_id =item_dict['sku_id'],
                                                               status =item_dict['status'],
                                                               )
            item_modified = datetime.dateime.strptime(item_dict['modified'],'%Y-%m-%d %H:%M:%S')
            if state or item_notify.modifid < item_modified:
                for k,v in item_dict.iteritems():
                    hasattr(item_notify,k) and setattr(item_notify,k,v)
                item_notify.save()
            process_item_notify_task.s(item_notify.id)
        #退款消息处理
        if item.has_key('notify_refund'):
            refund_dict = item['notify_refund']
            refund_notify,state = NotifyRefund.objects.get_or_create(
                                                                   user_id=refund_dict['user_id'],
                                                                   tid=refund_dict['tid'],
                                                                   oid=refund_dict['oid'],
                                                                   rid=refund_dict['rid'],
                                                                   status=refund_dict['status'],
                                                                   )
            refund_modified = datetime.dateime.strptime(refund_dict['modified'],'%Y-%m-%d %H:%M:%S')
            if state or refund_notify.modifid < refund_modified:
                for k,v in refund_dict.iteritems():
                    hasattr(refund_notify,k) and setattr(refund_notify,k,v)
                refund_notify.save()
            process_refund_notify_task.s(refund_notify.id)
    
        
        
        