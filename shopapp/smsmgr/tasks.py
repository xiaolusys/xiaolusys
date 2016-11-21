# -*- coding:utf-8 -*-
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

import random
import datetime
from django.db.models import F
from common.utils import update_model_fields
from flashsale.pay.models import Register
from shopapp.smsmgr.apis import send_sms_message, SMS_TYPE

import logging
logger = logging.getLogger(__name__)

@app.task()
def task_notify_package_post(package_order):
    """
    :param package_order: PackageOrder instance
    功能: 用户的订单发货了, 发送发货的短信通知 , package_order 称重的时候触发此任务执行.
    """

    package_sku_item = package_order.package_sku_items.first()
    if not package_sku_item:
        return

    now = datetime.datetime.now()
    delay_days = (now - package_sku_item.pay_time).days

    if delay_days <= 3:
        sms_notify_type = SMS_TYPE.SMS_NOTIFY_POST
    else:
        sms_notify_type = SMS_TYPE.SMS_NOTIFY_DELAY_POST

    mobiles = package_order.receiver_mobile
    params = {
        'sms_title': package_sku_item.title.split("/")[0],
        'sms_delay': '%d'%delay_days,
        'sms_logistic': package_order.logistics_company.name,
        'sms_logistic_no': package_order.out_sid,
        'sms_tips': '',
    }
    success = send_sms_message(mobiles, msg_type=sms_notify_type, **params)
    if success:
        package_order.is_send_sms = True
        update_model_fields(package_order, update_fields=['is_send_sms'])



@app.task()
def task_notify_lack_refund(sale_order):
    """
    :param package_order: PackageOrder instance
    功能: 用户的订单发货了, 发送发货的短信通知 , package_order 称重的时候触发此任务执行.
    """
    mobiles = sale_order.sale_trade.receiver_mobile
    params = {
        'sms_title': sale_order.title,
        'sms_payment': '%.1f'%sale_order.payment,
    }
    send_sms_message(mobiles, msg_type=SMS_TYPE.SMS_NOTIFY_LACK_REFUND, **params)


@app.task()
def task_register_code(mobile, send_type="1"):
    """ 短信验证码 """
    # 选择默认短信平台商，如果没有，任务退出
    try:
        reg = Register.objects.filter(vmobile=mobile).order_by('-modified')[0]
        if not reg.verify_code:
            raise Exception('send invalid code error: mobile=%s'%mobile)

        if send_type == "1":
            msg_type = SMS_TYPE.SMS_NOTIFY_REGISTER_CODE
        elif send_type == "2":
            msg_type = SMS_TYPE.SMS_NOTIFY_REGISTER_CODE
        elif send_type == "3":
            msg_type = SMS_TYPE.SMS_NOTIFY_REGISTER_CODE
        elif send_type == "4":
            msg_type = SMS_TYPE.SMS_NOTIFY_REGISTER_CODE
        else:
            return

        params = {
            'sms_code': reg.verify_code,
        }

        # 创建一条短信发送记录
        send_sms_message(mobile, msg_type=msg_type, **params)

    except Exception, exc:
        logger.error('%s'%exc.message, exc_info=True)
