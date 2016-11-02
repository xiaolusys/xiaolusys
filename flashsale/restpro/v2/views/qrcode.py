# encoding=utf8
from datetime import date
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework import (
    authentication,
    permissions,
    exceptions,
)
from django.core.cache import cache
from celery.result import AsyncResult

from flashsale.pay.models.user import Customer
from flashsale.xiaolumm.models import XiaoluMama
from shopapp.weixin.utils import fetch_wxpub_mama_custom_qrcode_url

import logging
logger = logging.getLogger(__name__)


class QRcodeViewSet(viewsets.ModelViewSet):
    """
    ## GET /rest/v2/qrcode/get_wxpub_qrcode　　根据小鹿妈妈 id 创建小鹿美美公众号临时二维码
    params:
    - mama_id  可选。默认未当前用户妈妈，传入可获取指定mama_id的二维码

    return:
    {
        "info": "",
        "code": 0,
        "qrcode_link": "http://7xrst8.com2.z0.glb.qiniucdn.com/qrcode/*.jpg"
    }
    """

    queryset = Customer.objects.all()
    # authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    # permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    @list_route()
    def get_wxpub_qrcode(self, request, *args, **kwargs):
        mama_id = request.GET.get('mama_id', '')

        if not mama_id:
            customer = Customer.getCustomerByUser(user=request.user)
            if not customer:
                return Response({"code": 7, "info": u"用户未找到"})

            mama = customer.get_xiaolumm()
            if not mama:
                return Response({"code": 2, "info": u"不是小鹿妈妈"})
            mama_id = mama.id
        else:
            mama = XiaoluMama.objects.filter(id=mama_id).first()
            if not mama:
                return Response({"code": 2, "info": u"不是小鹿妈妈"})

        resp = {
            'code': 0,
            'info': u'',
            'qrcode_link': ''
        }
        cache_key = 'wxpub_xiaolumm_mama_referal_qrcode_mama_id_%s' % mama_id
        cache_value = cache.get(cache_key)

        qrcode_url = cache_value.get('qrcode_url', '') if cache_value else ''
        task_id = cache_value.get('task_id', '') if cache_value else ''

        if qrcode_url:
            resp['qrcode_link'] = qrcode_url
            resp['task_id'] = task_id
        elif task_id:
            task = AsyncResult(task_id)
            if task.status == 'FAILURE':
                task = fetch_wxpub_mama_custom_qrcode_url.apply_async(
                    args=[mama_id], queue='qrcode',
                    routing_key='weixin.task_create_mama_referal_qrcode_and_response_url')
                resp['task_id'] = task.id
                cache.set(cache_key, {'qrcode_url': task.result, 'task_id': task.id}, 3600)
            else:
                resp['qrcode_link'] = task.result or ''
                resp['task_id'] = task_id
                cache.set(cache_key, {'qrcode_url': task.result, 'task_id': task_id}, 3600)
        else:
            task = fetch_wxpub_mama_custom_qrcode_url.apply_async(
                args=[mama_id], queue='qrcode',
                routing_key='weixin.task_create_mama_referal_qrcode_and_response_url')
            resp['task_id'] = task.id
            cache.set(cache_key, {'qrcode_url': task.result, 'task_id': task.id}, 3600)

        logger.info({
            'action': 'api.v2.qrcode.get_wxpub_qrcode',
            'mama_id': mama_id,
            'qrcode_link': qrcode_url,
            'task_id': task_id
        })
        return Response(resp)

    def retrieve(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def destroy(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')
