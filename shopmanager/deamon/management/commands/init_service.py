#-*- coding:utf8 -*-
import datetime
from daemonextension import DaemonCommand
from django.core.management import call_command
from shopback.users.models import User
from shopback.orders.tasks import saveUserDuringOrdersTask
from shopback.fenxiao.tasks import saveUserPurchaseOrderTask
from shopback import paramconfig as pcfg
from auth import apis
import logging

logger = logging.getLogger('initservice.handler')

def now2str():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

class Command(DaemonCommand):

    def handle_daemon(self, *args, **options):

        print '【%s】:-----------------------------系统服务设置开始-----------------------------'.decode('utf8')%now2str()
        users = User.objects.all()
        for user in users:
                print '【%s】:--------------开始设置%s--------------'.decode('utf8')%(now2str(),user.nick)

                try:
                    response = apis.taobao_increment_customer_permit(type='get,syn,notify',topics='trade;refund;item',
                                                        status='all;all;ItemAdd,ItemUpdate',tb_user_id=user.visitor_id)
                except:
                    print '【%s】:主动消息服务授权失败'.decode('utf8')%now2str()
                    logger.error(exc.message,exc_info=True)
                    return 
                else:                
                    print '【%s】:主动消息服务授权成功'.decode('utf8')%now2str()
                    modified = response['increment_customer_permit_response']['app_customer']['created']
                    created = datetime.datetime.strptime(modified,'%Y-%m-%d %H:%M:%S')+datetime.timedelta(0,30,0)
                    User.objects.filter(id=user.id).update(item_notify_updated=created,trade_notify_updated=created,refund_notify_updated=created)
                
                print '【%s】:开始下载商城待发货订单'.decode('utf8')%now2str()
                try:
                    saveUserDuringOrdersTask(user.visitor_id,status=pcfg.WAIT_SELLER_SEND_GOODS)
                except Exception,exc:
                    print '【%s】:下载商城待发货订单失败'.decode('utf8')%now2str()
                    logger.error(exc.message,exc_info=True)
                    return 
                else:
                    print '【%s】:下载商城待发货订单成功'.decode('utf8')%now2str()
                
                print '【%s】:开始下载分销待发货订单'.decode('utf8')%now2str()    
                try:
                    saveUserPurchaseOrderTask(user.visitor_id,status=pcfg.WAIT_SELLER_SEND_GOODS)
                except Exception,exc:
                    print '【%s】:下载分销待发货订单失败'.decode('utf8')%now2str()
                    logger.error(exc.message,exc_info=True)
                    return 
                else:
                    print '【%s】:下载分销待发货订单成功'.decode('utf8')%now2str()
         

            
