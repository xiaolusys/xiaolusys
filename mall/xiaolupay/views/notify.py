# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.http import HttpResponse

import datetime
from ..models.charge import Credential
from ..libs.wxpay.app import WXPay
from ..services.charge import retrieve_or_update_order

import logging
logger = logging.getLogger(__name__)



def pay_channel_notify(request, channel):

    content = request.POST.dict() or request.body
    logger.info({
        'action': 'notify',
        'channel': channel,
        'data': content,
        'action_time': datetime.datetime.now()
    })
    if not content:
        return HttpResponse('no params')

    if channel in ('alipay', 'alipay_wap'):
        order_no = content['out_trade_no']

        credential = Credential.objects.filter(order_no=order_no, channel__in=('alipay', 'alipay_wap'))\
            .order_by('-created').first()
        channel = credential.channel

    elif channel in ('wx', 'wx_pub'):
        content = WXPay.process_wxpay_response(content)
        order_no = content['out_trade_no']
    else:
        order_no = ''

    retrieve_or_update_order(order_no, channel=channel ,notify_order_info=content)

    return HttpResponse('success')



