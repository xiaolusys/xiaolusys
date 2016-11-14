# coding:utf-8
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Sum
from django.conf import settings
from django.views.generic import View

from rest_framework.renderers import JSONRenderer
from core.options import log_action, ADDITION, CHANGE

from flashsale.pay.models import Envelop

class EnvelopConfirmSendView(View):
    renderer_classes = (JSONRenderer,)

    def post(self, request, *args, **kwargs):

        content = request.POST
        origin_url = content.get('origin_url')
        envelop_ids = content.get('envelop_ids', '').split(',')
        secret = content.get('secret')

        admin_email = settings.MANAGERS[0][1]
        if secret.strip() != admin_email:
            messages.add_message(request, messages.ERROR, u'请输入正确的红包发送暗号！')
            return redirect(origin_url)

        envelop_qs = Envelop.objects.filter(id__in=envelop_ids, status__in=(Envelop.WAIT_SEND, Envelop.FAIL))

        try:
            for envelop in envelop_qs:
                envelop.send_envelop()
                log_action(request.user.id, envelop, CHANGE, u'发送红包')
        except Exception, exc:
            messages.add_message(request, messages.ERROR, u'红包发送异常:%s' % (exc.message))

        envelop_goodqs = Envelop.objects.filter(id__in=envelop_ids, status=Envelop.CONFIRM_SEND)
        envelop_count = envelop_goodqs.count()
        total_amount = envelop_goodqs.aggregate(total_amount=Sum('amount')).get('total_amount') or 0

        messages.add_message(request, messages.INFO, u'已成功发送 %s 个红包，总金额：%s！' % (envelop_count, total_amount / 100.0))

        return redirect(origin_url)