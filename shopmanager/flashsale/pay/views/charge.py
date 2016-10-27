# -*- encoding:utf8 -*-
import json
from django.conf import settings
from django.db import IntegrityError, models
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.generic import View

from flashsale.pay import tasks
import pingpp

import logging
logger = logging.getLogger(__name__)


class PINGPPCallbackView(View):
    def post(self, request, *args, **kwargs):
        content = request.body
        logger.info('pingpp callback:%s' % content)

        try:
            # 读取异步通知数据
            message = json.loads(content)
        except Exception, exc:
            logger.error('pingpp callback loaddata: %s, %s' % (content, exc), exc_info=True)
            return HttpResponse('no params')

        data = message.get('data')
        if not data:
            return HttpResponse('no data')

        notify = data['object']
        response = 'success'

        # 对异步通知做处理
        if 'object' not in notify:
            response = 'fail'
        else:
            if notify['object'] == 'charge':
                # 开发者在此处加入对支付异步通知的处理代码
                if settings.DEBUG:
                    tasks.notifyTradePayTask(notify)
                else:
                    tasks.notifyTradePayTask.delay(notify)

            elif notify['object'] == 'refund':
                # 开发者在此处加入对退款异步通知的处理代码
                if settings.DEBUG:
                    tasks.notifyTradeRefundTask(notify)
                else:
                    tasks.notifyTradeRefundTask.delay(notify)

            elif notify['object'] == 'red_envelope':
                tasks.task_handle_envelope_notify.delay(notify)
            else:
                response = 'fail'
        if response != 'success':
            logger.error('pingpp callback response fail: %s'% content)
        return HttpResponse(response)

    get = post


########## alipay callback ###########
class PayResultView(View):
    def get(self, request, *args, **kwargs):
        content = request.REQUEST
        logger.info('pay result:%s' % content)

        return HttpResponseRedirect(reverse('user_orderlist'))


class WXPayWarnView(View):
    def post(self, request, *args, **kwargs):
        content = request.body
        logger.error('wx warning:%s' % content)
        return HttpResponse('ok')

    get = post