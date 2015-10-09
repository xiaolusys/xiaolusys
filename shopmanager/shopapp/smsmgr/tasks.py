#-*- coding:utf8 -*-
import datetime
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from django.db.models import Q,F
from django.template import Context, Template
from shopback.items.models import Product,ProductSku
from shopback.trades.models import MergeTrade
from shopapp.smsmgr.models import SMSPlatform,SMSRecord,SMSActivity,SMS_NOTIFY_POST,SMS_NOTIFY_BIRTH, SMS_NOTIFY_VERIFY_CODE, SMS_NOTIFY_GOODS_LATER
from shopapp.smsmgr.service import SMS_CODE_MANAGER_TUPLE
from shopback import paramconfig as pcfg
from common.utils import update_model_fields,single_instance_task
import logging

logger = logging.getLogger('smsmgr.handler')

POST_NOTIFY_TITLE = '订单发货客户提示'

#POST_CONTENT_SEND_LATER = "亲爱的小鹿美美用户您好:亲在{0}购买的{1}产品,因供应商换季非常时期未按时发货给亲带来不便,小鹿美美深表歉意,请耐心等待,如有疑问请联系(优尼世界公众号-我的--我的客服)会为您解答疑问,小鹿美美在此祝您生活愉快."
#POST_CONTENT_SEND_LATER1 = "尊敬的大人，您订购的{0}在入库检查时发现略有瑕疵，小的正在联系工厂紧急调货 ！望大人息怒，如有疑问请联系客服，么么哒~"
#POST_CONTENT_SEND_LATER2 = "阁下所购宝物{0}由于成色原因暂未通过质检要求，本府已连夜派兵紧急调货！未能如期交货，望阁下海涵，如有疑问请联系客服，么么哒~"
#POST_CONTENT_SEND_LATER3 = "启奏圣上：您所托宝贝{0}在入库检查时发现尺码略有偏差，本店已联系厂家换货，还望圣上饶恕！如有疑问请联系小鹿客服，么么哒~"

POST_CONTENT_SEND_LATER1 = "亲爱的顾客，您订购的{0}在入库检查时发现尺码略有偏差，本店正在加紧调货，如有疑问请联系我们平台客服，么么哒～"
POST_CONTENT_SEND_LATER2 = "亲爱的顾客，您订购的{0}由于商品成色原因未通过质检要求，本店正在加紧调货，如有疑问请联系我们平台客服，么么哒～"
POST_CONTENT_SEND_LATER3 = "亲爱的顾客，您订购的{0}在入库检查时发现包装部分污损，本店正在加紧调货，如有疑问请联系我们平台客服，么么哒～"


def get_smsg_from_trade(trade):
    """ 获取商品客户提示 """
    
    sms_tmpl = SMSActivity.objects.filter(sms_type=SMS_NOTIFY_POST,status=True)
    if sms_tmpl.count() == 0:
        return ''
    
    ms  = set()
    for o in trade.inuse_orders:
        outer_sku_id = o.outer_sku_id
        outer_id     = o.outer_id
        prod_sku = None
        prod     = None
        try:
            prod = Product.objects.get(outer_id=outer_id)
            if outer_sku_id:
                prod_sku = ProductSku.objects.get(outer_id=outer_sku_id,product=prod)
        except:
            pass
        #同一规格提示只能出现一次
        if prod_sku and prod_sku.buyer_prompt.strip():
            ms.add(prod_sku.buyer_prompt.strip())
        #同一商品提示只能出现一次    
        elif prod and prod.buyer_prompt.strip():
            ms.add(prod.buyer_prompt.strip())

    dt   = datetime.datetime.now()
    tmpl = Template(sms_tmpl[0].text_tmpl)
    trade_dict = {'tid':trade.tid,
                  'buyer_nick':trade.buyer_nick,
                  'seller_nick':trade.user.nick,
                  'weight':trade.weight,
                  'logistic_name':trade.logistics_company.name.replace(u'热敏',u'快递'),
                  'out_sid':trade.out_sid}
    c    = Context({'trade':trade_dict,'prompt_msg':','.join(ms),'today_date':dt})
    
    return tmpl.render(c)


@task
def notifyBuyerPacketPostTask(trade_id,platform_code):
    """ 短信通知收货人，包裹发出信息 """
    try:
        trade     = MergeTrade.objects.get(id=trade_id)
        if trade.is_send_sms:
            return
        
        platform  = SMSPlatform.objects.get(code=platform_code)
        
        content = get_smsg_from_trade(trade)
        if not  content:
            return 
        
        params = {}
        params['content'] = content
        params['userid']  = platform.user_id
        params['account'] = platform.account
        params['password'] = platform.password
        params['mobile']   = trade.receiver_mobile
        params['taskName'] = POST_NOTIFY_TITLE
        params['mobilenumber']    = 1
        params['countnumber']     = 1
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
            update_model_fields(trade,update_fields=['is_send_sms'])
    except Exception,exc:
        logger.error(exc.message or 'empty error',exc_info=True)
    

@single_instance_task(60*60,prefix='shopapp.smsmgr.tasks.')
def notifyPacketPostTask(days):
    
    #选择默认短信平台商，如果没有，任务退出
    try:
        platform = SMSPlatform.objects.get(is_default=True)
    except:
        return 
    
    dt  = datetime.datetime.now()
    df  = dt - datetime.timedelta(days=days)
    wait_sms_trades = MergeTrade.objects.filter(type__in=(pcfg.FENXIAO_TYPE,
                                                          pcfg.TAOBAO_TYPE,
                                                          pcfg.COD_TYPE,
                                                          pcfg.WX_TYPE,
                                                          pcfg.SALE_TYPE),
        sys_status=pcfg.FINISHED_STATUS,is_send_sms=False,weight_time__gte=df, weight_time__lte=dt,
        is_express_print=True).exclude(receiver_mobile='')#

    for trade in wait_sms_trades:
        subtask(notifyBuyerPacketPostTask).delay(trade.id,platform.code)

@task
def getupMorningLockTask():    
    
    #选择默认短信平台商，如果没有，任务退出
    try:
        platform = SMSPlatform.objects.get(is_default=True)
    except:
        return 
    
    sms_manager  = dict(SMS_CODE_MANAGER_TUPLE).get(platform.code,None)
    sms_tmpl     = SMSActivity.objects.filter(sms_type=SMS_NOTIFY_BIRTH,status=True)
    sms_ins      = sms_tmpl[0]
    
    status  = sms_ins.text_tmpl[0]
    
    params = {}
    params['content'] = sms_ins.text_tmpl[1:-1]
    params['userid']  = platform.user_id
    params['account'] = platform.account
    params['password'] = platform.password
    params['mobile']   = '15941103294'#13917170476
    params['taskName'] = '起床了'
    params['mobilenumber']    = 1
    params['countnumber']     = 1
    params['telephonenumber'] = 0
    
    params['action'] = 'send'
    params['checkcontent'] = '0'
    
    manager = sms_manager()
    
    manager.batch_send(**params)
    
from flashsale.pay.models_user import Register
@task
def task_register_code(mobile, send_type="1"):
    """ 短信验证码 """
    #选择默认短信平台商，如果没有，任务退出
    try:
        platform = SMSPlatform.objects.get(is_default=True)
    except:
        return
    try:

        register_v = Register.objects.get(vmobile=mobile)
        if send_type == "1":
            content = u"注册验证码为：" + register_v.verify_code + "，请在页面输入完成验证。如非本人操作请忽略。 --小鹿美美"
        elif send_type == "2":
            content = u"您设置新密码的验证码：" + register_v.verify_code + "，请即时输入，为保证您的账户安全，请勿外泄。如有疑问请致电021-50939326【小鹿美美】"
        elif send_type == "3":
            content = u"您绑定手机的验证码：" + register_v.verify_code + "，请在页面输入完成验证。如非本人操作请忽略。 --小鹿美美"
        if not content:
            return
        params = {}
        params['content'] = content
        params['userid'] = platform.user_id
        params['account'] = platform.account
        params['password'] = platform.password
        params['mobile'] = mobile
        params['taskName'] = "小鹿美美验证码"
        params['mobilenumber'] = 1
        params['countnumber'] = 1
        params['telephonenumber'] = 0

        params['action'] = 'send'
        params['checkcontent'] = '0'

        sms_manager = dict(SMS_CODE_MANAGER_TUPLE).get(platform.code, None)
        if not sms_manager:
            raise Exception('未找到短信服务商接口实现')

        manager = sms_manager()
        success = False

        #创建一条短信发送记录
        sms_record = manager.create_record(params['mobile'], params['taskName'], SMS_NOTIFY_VERIFY_CODE, params['content'])
        #发送短信接口
        try:
            success, task_id, succnums, response = manager.batch_send(**params)
        except Exception, exc:
            sms_record.status = pcfg.SMS_ERROR
            sms_record.memo = exc.message
            logger.error(exc.message,exc_info=True)
        else:
            sms_record.task_id = task_id
            sms_record.succnums = succnums
            sms_record.retmsg = response
            sms_record.status = success and pcfg.SMS_COMMIT or pcfg.SMS_ERROR
        sms_record.save()
        if success:
            SMSPlatform.objects.filter(code=platform.code).update(sendnums=F('sendnums')+int(succnums))
            register_v.verify_count += 1
            register_v.save()
    except Exception,exc:
        logger.error(exc.message or 'empty error',exc_info=True)

from shopback.trades.models import SendLaterTrade
@task
def task_deliver_goods_later():
    """ 付款五天未发货通知 """
    try:
        import datetime
        today = datetime.date.today()
        all_trade = MergeTrade.objects.filter(
            sys_status__in=(MergeTrade.WAIT_PREPARE_SEND_STATUS,
                           MergeTrade.WAIT_AUDIT_STATUS,
                           MergeTrade.WAIT_CHECK_BARCODE_STATUS,
                           MergeTrade.WAIT_SCAN_WEIGHT_STATUS,
                           MergeTrade.REGULAR_REMAIN_STATUS)).\
            filter(status=MergeTrade.WAIT_SELLER_SEND_GOODS)
        all_trade = all_trade.filter(pay_time__gte=today - datetime.timedelta(days=5),
                                     pay_time__lt=today - datetime.timedelta(days=4))
        for trade in all_trade:
            already_send = SendLaterTrade.objects.filter(trade_id=trade.id, success=True)
            if already_send.count() == 0:
                func2send_message(trade)
    except Exception, exc:
        logger.error(exc.message or 'empty error', exc_info=True)

import random
def func2send_message(trade):
    #选择默认短信平台商，如果没有，任务退出
    try:
        platform = SMSPlatform.objects.get(is_default=True)
    except:
        return
    try:
        mobile = trade.receiver_mobile
        if not mobile or len(mobile) != 11:
            return

        all_order = trade.merge_orders.all()
        if all_order.count() == 0:
            return
        title = all_order[0].title.split("/")[0]

        content = random.choice([POST_CONTENT_SEND_LATER1, POST_CONTENT_SEND_LATER2, POST_CONTENT_SEND_LATER3]).format(
            title.encode('utf-8'))
        if not content:
            return
        params = {}
        params['content'] = content
        params['userid'] = platform.user_id
        params['account'] = platform.account
        params['password'] = platform.password
        params['mobile'] = mobile
        params['taskName'] = "小鹿美美五天发货通知"
        params['mobilenumber'] = 1
        params['countnumber'] = 1
        params['telephonenumber'] = 0

        params['action'] = 'send'
        params['checkcontent'] = '0'

        sms_manager = dict(SMS_CODE_MANAGER_TUPLE).get(platform.code, None)
        if not sms_manager:
            raise Exception('未找到短信服务商接口实现')

        manager = sms_manager()
        success = False

        #创建一条短信发送记录
        sms_record = manager.create_record(params['mobile'], params['taskName'], SMS_NOTIFY_GOODS_LATER, params['content'])
        #发送短信接口
        try:
            success, task_id, succnums, response = manager.batch_send(**params)
        except Exception,exc:
            sms_record.status = pcfg.SMS_ERROR
            sms_record.memo = exc.message
            logger.error(exc.message,exc_info=True)
        else:
            sms_record.task_id = task_id
            sms_record.succnums = succnums
            sms_record.retmsg = response
            sms_record.status = success and pcfg.SMS_COMMIT or pcfg.SMS_ERROR
        sms_record.save()

        if success:
            SMSPlatform.objects.filter(code=platform.code).update(sendnums=F('sendnums')+int(succnums))
            #记录是否发送
            send_success = SendLaterTrade(trade_id=trade.id, success=True)
            send_success.save()
    except Exception, exc:
        logger.error(exc.message or 'empty error', exc_info=True)