# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.http import HttpResponse

from ..libs.alipay.app import AliPay
from ..libs.wxpay.app import WXPay
from ..services.charge import retrieve_or_update_order

import logging
logger = logging.getLogger(__name__)

def alipay_notify(request):

    content = dict(request.POST.iterlists())
    logger.info({
        'action': 'notify',
        'channel': 'alipay',
        'data': content,
    })
    if not content:
        return HttpResponse('no params')

    alipay = AliPay()
    params = alipay.process_alipay_response(content)
    order_no = params['out_trade_no']
    retrieve_or_update_order(order_no, notify_order_info=params)

    return HttpResponse('success')

def wxpay_notify(request):
    content = request.body
    logger.info({
        'action': 'notify',
        'channel': 'wxpay',
        'data': content,
    })
    if not content:
        return HttpResponse('no params')

    params = WXPay.process_wxpay_response(content)
    order_no = params['out_trade_no']
    retrieve_or_update_order(order_no, notify_order_info=params)

    return HttpResponse('success')


