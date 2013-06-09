#-*- coding:utf8 -*-
import datetime
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from django.db.models import Q,F
from django.template.loader import render_to_string
from shopback.items.models import Product,ProductSku
from shopback.trades.models import MergeTrade
from shopapp.smsmgr.models import SMSPlatform,SMSRecord,SMS_NOTIFY_POST
from shopapp.smsmgr.service import SMS_CODE_MANAGER_TUPLE
from shopback import paramconfig as pcfg
from utils import update_model_feilds
from auth import apis
import logging

logger = logging.getLogger('smsmgr.handler')

POST_NOTIFY_TITLE = '订单发货客户提示'

def get_smsg_from_trade(trade):
    """ 获取商品客户提示 """
    prompt_msg = ''
    for o in trade.inuse_orders:
        
        outer_sku_id = o.outer_sku_id
        outer_id     = o.outer_id
        prod_sku = None
        prod     = None
        try:
            if outer_sku_id:
                prod_sku = ProductSku.objects.get(outer_id=outer_sku_id,product__outer_id=outer_id)
            prod = Product.objects.get(outer_id=outer_id)
        except:
            pass
        
        prompt_msg += (prod_sku and prod_sku.buyer_prompt) or (prod and prod.buyer_prompt) or '' 
    dt  = datetime.datetime.now()
    sms_text   = render_to_string('sms/notify_packet_post_template.txt',
                                  {'trade':trade,'prompt_msg':prompt_msg,'today_date':dt})
    return sms_text


@task
def notifyBuyerPacketPostTask(trade_id,platform_code):
    """ 短信通知收货人，包裹发出信息 """
    try:
        trade     = MergeTrade.objects.get(id=trade_id)
        if trade.is_send_sms:
            return
        
        platform  = SMSPlatform.objects.get(code=platform_code)
        
        params = {}
        params['content'] = get_smsg_from_trade(trade)
        params['userid']  = platform.user_id
        params['account'] = platform.account
        params['password'] = platform.password
        params['mobile']   = trade.receiver_mobile
        params['taskName'] = POST_NOTIFY_TITLE
        params['mobilenumber'] = 1
        params['countnumber']  = 1
        params['telephonenumber'] = 0
        
        params['action'] = 'send'
        params['checkcontent'] = '0'
        
        sms_manager = dict(SMS_CODE_MANAGER_TUPLE).get(platform_code,None)
        if not sms_manager:
            raise Exception('未找到短信服务商接口实现')
        
        manager = sms_manager()
        success = False

        #创建一条短信发送记录
        sms_record = manager.create_record(params['mobile'],params['taskName'],SMS_NOTIFY_POST,params['content'])
        #发送短信接口
        try:
            success,task_id,succnums,response = manager.batch_send(**params)
        except Exception,exc:
            sms_record.status = pcfg.SMS_ERROR
            sms_record.memo   = exc.message
            logger.error(exc.message,exc_info=True)
        else:
            sms_record.task_id  = task_id
            sms_record.succnums = succnums
            sms_record.retmsg   = response
            sms_record.status   =  success and pcfg.SMS_COMMIT or pcfg.SMS_ERROR
        sms_record.save()
        
        if success:
            SMSPlatform.objects.filter(code=platform_code).update(sendnums=F('sendnums')+int(succnums))
            trade.is_send_sms = True
            update_model_feilds(trade,update_fields=['is_send_sms'])
    except Exception,exc:
        logger.error(exc.message or 'empty error',exc_info=True)
    

@apis.single_instance_task(60*60,prefix='shopapp.smsmgr.tasks.')
def notifyPacketPostTask(days):
    
    #选择默认短信平台商，如果没有，任务退出
    try:
        platform = SMSPlatform.objects.get(is_default=True)
    except:
        return 
    
    dt  = datetime.datetime.now()
    df  = dt - datetime.timedelta(0,60*60*13*days,0)
    wait_sms_trades = MergeTrade.objects.filter(type__in=(pcfg.FENXIAO_TYPE,pcfg.TAOBAO_TYPE,pcfg.COD_TYPE),
        sys_status=pcfg.FINISHED_STATUS,is_send_sms=False,weight_time__gte=df, weight_time__lte=dt,
        is_express_print=True).exclude(receiver_mobile='') #

    for trade in wait_sms_trades:
        
        subtask(notifyBuyerPacketPostTask).delay(trade.id,platform.code)

    
    