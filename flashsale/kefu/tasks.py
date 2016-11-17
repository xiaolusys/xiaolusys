# -*- encoding:utf8 -*-
from __future__ import division, absolute_import, unicode_literals

import json
import datetime

from django.core.serializers.json import DjangoJSONEncoder
from shopmanager import celery_app as app

from flashsale.kefu.models import KefuPerformance
from flashsale.pay.models import SaleRefund
from supplychain.supplier.models import SaleProduct, SaleSupplier, SupplierCharge

import logging
logger = logging.getLogger('celery.handler')


@app.task(max_retries=1, default_retry_delay=5)
def task_record_kefu_performance(start_date, end_date, record_type="0"):
    """客服操作"""
    try:
        year, month, day = start_date.split('-')
        start_date_time = datetime.datetime(int(year), int(month), int(day))
        year, month, day = end_date.split('-')
        end_date_time = datetime.datetime(int(year), int(month), int(day), 23, 59, 59)
        if record_type == "0":
            all_record = KefuPerformance.objects.filter(operate_time__range=(start_date_time, end_date_time)).order_by(
                "-operate_time")

        else:
            all_record = KefuPerformance.objects.filter(operate_time__range=(start_date_time, end_date_time),
                                                        operation=record_type).order_by("-operate_time")
        result_data = []
        summary_data = {}
        for one_record in all_record:
            temp_dict = {"kefu": one_record.kefu_name, "operate": one_record.get_operation_display(),
                         "operate_time": one_record.operate_time, "trade_id": one_record.trade_id}
            temp_dict = json.dumps(temp_dict, cls=DjangoJSONEncoder)
            result_data.append(temp_dict)
            if one_record.kefu_name not in summary_data:
                summary_data[one_record.kefu_name] = [0, 0, 0]
            if one_record.operation == KefuPerformance.CHECK:
                summary_data[one_record.kefu_name][0] += 1
            if one_record.operation == KefuPerformance.REVIEW:
                summary_data[one_record.kefu_name][1] += 1
            if one_record.operation == KefuPerformance.DELAY:
                summary_data[one_record.kefu_name][2] += 1


    except Exception, exc:
        raise task_record_kefu_performance.retry(exc=exc)
    return {"result_data": result_data, "summary_data": summary_data}


from shopapp.smsmgr.models import SMSPlatform, SMS_NOTIFY_GOODS_LACK
from shopapp.smsmgr.service import SMS_CODE_MANAGER_TUPLE
from shopback import paramconfig as pcfg
from django.db.models import F


@app.task()
def task_send_message(content, mobile):
    """发送短信"""
    # 选择默认短信平台商，如果没有，任务退出
    try:
        platform = SMSPlatform.objects.get(is_default=True)
    except:
        return
    try:
        if not mobile or len(mobile) != 11:
            return
        if not content:
            return
        params = {}
        params['content'] = content
        params['userid'] = platform.user_id
        params['account'] = platform.account
        params['password'] = platform.password
        params['mobile'] = mobile
        params['taskName'] = "小鹿美美缺货通知"
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

        # 创建一条短信发送记录
        sms_record = manager.create_record(params['mobile'], params['taskName'], SMS_NOTIFY_GOODS_LACK,
                                           params['content'])
        # 发送短信接口
        try:
            success, task_id, succnums, response = manager.batch_send(**params)
        except Exception, exc:
            sms_record.status = pcfg.SMS_ERROR
            sms_record.memo = exc.message
            logger.error(exc.message, exc_info=True)
        else:
            sms_record.task_id = task_id
            sms_record.succnums = succnums
            sms_record.retmsg = response
            sms_record.status = success and pcfg.SMS_COMMIT or pcfg.SMS_ERROR
        sms_record.save()

        if success:
            SMSPlatform.objects.filter(code=platform.code).update(sendnums=F('sendnums') + int(succnums))
    except Exception, exc:
        logger.error(exc.message or 'empty error', exc_info=True)
