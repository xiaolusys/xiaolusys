# coding: utf8
from __future__ import absolute_import, unicode_literals

import  datetime
import base64
import Image
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
            logger.info({
                'action': 'idcard_indentify',
                'action_time': datetime.datetime.now(),
                'code': 1,
                'message': 'side和card_base64参数不能为空',
            })
            return Response({'code':1, 'info': 'side和card_base64参数不能为空'})

        try:
            resp = idcard.identify(card_side, card_base64)
        except Exception, exc:
            logger.error({
                'action': 'idcard_indentify',
                'action_time': datetime.datetime.now(),
                'code': 2,
                'message': '请求异常:%s'%str(exc),
            }, exc_info=True)
            return Response({'code': 2, 'info': '请求异常:%s'%str(exc)})

        if not resp['success']:
            logger.info({
                'action': 'idcard_indentify',
                'action_time': datetime.datetime.now(),
                'code': 3,
                'message': '未识别成功, 请调整位置重新拍摄',
            })
            return Response({'code': 3, 'info': '未识别成功, 请调整位置重新拍摄'})

        # 对身份证拍摄角度做一些限制,保证身份证照片清晰度
        if card_side == 'face':
            center = resp['face_rect']['center']
            ract_angle = abs(resp['face_rect']['angle'])
            h_size_x, h_size_y = resp['face_rect']['size']['height'], resp['face_rect']['size']['width']
            img = Image.open(StringIO(base64.b64decode(card_base64)))
            img_size = img.size
            # １,图片距离边框两边的距离不能超过图片总宽度的20%, 头像高度不能小于10像素, 图片拍摄倾斜角度不能超过20度
            # if (img_size[0] - h_size_x - center['x']) > 0.2 * img_size[0] or h_size_y < 10 or 20 < ract_angle % 90 < 60:
            #     logger.info({
            #         'action': 'idcard_indentify',
            #         'action_time': datetime.datetime.now(),
            #         'code': 4,
            #         'message': '未识别成功: img_size=(%s,%s)'%(img_size[0], img_size[1]),
            #         'data': resp,
            #         'image_size': img_size,
            #     })
            #     return Response({'code': 4, 'info': '请在明光下拍摄，并调整角度至边框平行'})

            if (h_size_x * h_size_y * 1.0) / (img_size[0] * img_size[1]) < 0.015 or 20 < ract_angle % 90 < 60:
                logger.info({
                    'action': 'idcard_indentify',
                    'action_time': datetime.datetime.now(),
                    'code': 5,
                    'message': '未识别成功: img_size=(%s,%s)' % (img_size[0], img_size[1]),
                    'data': resp,
                    'image_size': img_size,
                })
                return Response({'code': 5, 'info': '请调整拍摄距离和角度让身份证居中'})

        customer = Customer.getCustomerByUser(request.user)
        resp.update({
            'side': card_side,
            'card_imgpath': 'ocr/idcard_%s_%s_%s.jpg'%(customer.id, card_side, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
         })

        #　TODO@MERON保存图片base64到七牛云存储
        try:
            upload_private_to_remote(resp['card_imgpath'], StringIO(base64.b64decode(card_base64)))
        except Exception, exc:
            logger.error('图片上传七牛错误:%s' % str(exc), exc_info=True)

        return Response({'code': 0, 'info':'', 'card_infos': resp})






