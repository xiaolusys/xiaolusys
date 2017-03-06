# coding: utf8
from __future__ import absolute_import, unicode_literals

import  datetime
import base64
from cStringIO import StringIO

from rest_framework import viewsets
from rest_framework import authentication, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from common.auth import WeAppAuthentication
from flashsale.pay.models.user import Customer
from core.ocr import idcard
from core.upload import upload_private_to_remote

import logging
logger = logging.getLogger(__name__)

class OcrIndentifyViewSet(viewsets.GenericViewSet):
    """
    """
    authentication_classes = (authentication.SessionAuthentication, WeAppAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (JSONRenderer, )

    @list_route(methods=['POST'])
    def idcard_indentify(self, request, *args, **kwargs):
        """
        :param request:
        :param args: side (face / back), card_base64
        :param kwargs:
        :return:{ side: 'face', 'card_no':'xxx', 'address':'xxx', 'name': 'xxx', 'face_imgurl': ''}
        """
        data = request.POST.dict()
        card_side = data.get('side') or 'face'
        card_base64 = data.get('card_base64') or ''

        if not card_base64 or not card_side:
            return Response({'code':1, 'info': 'object_id,side和card_base64参数不能为空'})

        try:
            resp = idcard.identify(card_side, card_base64)
        except Exception, exc:
            logger.error(str(exc), exc_info=True)
            return Response({'code': 2, 'info': '请求异常:%s'%str(exc)})

        if not resp['success']:
            return Response({'code': 3, 'info': '未识别成功, 请调整位置重新拍摄'})

        customer = Customer.getCustomerByUser(request.user)
        resp.update({
            'side': card_side,
            'card_imgpath': 'ocr/idcard_%s_%s.jpg'%(customer.id, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
         })

        #　TODO@MERON保存图片base64到七牛云存储
        try:
            upload_private_to_remote(resp['card_imgpath'], StringIO(base64.b64decode(card_base64)))
        except Exception, exc:
            logger.error('图片上传七牛错误:%s' % str(exc), exc_info=True)

        return Response({'code': 0, 'info':'', 'card_infos': resp})






