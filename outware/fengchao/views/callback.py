# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
import json
from rest_framework import viewsets
from rest_framework import authentication, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from outware.models import OutwareAccount
from outware.adapter.ware.push import pms, oms
from ... import constants
from core.apis.models import DictObject

import logging
logger = logging.getLogger(__name__)


class FengchaoCallbackViewSet(viewsets.GenericViewSet):
    """
    ## 蜂巢回调 API：
    ``` 接口响应 code = 0 表示成功, code > 0表示失败, info 为失败错误信息```
    > ### 采购单实收回传接口: [po_confirm]( ./callback/po_confirm.json ) 调用方法:POST;
    > ### 订单状态更新接口: [order_state]( ./callback/order_state.json ) 调用方法:POST;
    > ### 包裹确认发货接口: [order_delivery]( ./callback/order_delivery.json ) 调用方法:POST;
    """
    authentication_classes = []
    permission_classes = []
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer,)
    serializer_class = BaseSerializer

    def list(self, request, *args, **kwargs):
        return Response({'code': 0, 'info': 'success'})

    def verify_request(self, data):
        owapp = OutwareAccount.objects.filter(app_id=data.get('app_id','')).first()
        sign = data.pop('sign', '')
        return owapp and owapp.sign_verify(data, sign) or False

    @list_route(methods=['POST'])
    def po_confirm(self, request, *args, **kwargs):
        req_data = request.POST.dict()
        logger.info({
            'action': 'fengchao_poconfirm',
            'action_time': datetime.datetime.now(),
            'data': req_data,
        })
        if not self.verify_request(req_data):
            return Response({'code': 1, 'info': '签名无效'})

        try:
            data = json.loads(req_data['data'])
            order_code = data['order_code']

            order_type = (constants.ORDER_PURCHASE['code'], constants.ORDER_REFUND['code']
                )[data['order_type'].lower() == 'refund' and 1 or 0]
            params = {
                'order_code': order_code,
                'store_code': data['store_code'],
                'order_type': order_type,
                'inbound_skus': [],
                'object': 'OutwareInboundOrder',
            }

            for item in data['warehouse_warrant_items']:
                params['inbound_skus'].append({
                    'sku_code': item['sku_id'],
                    'batch_no': item['batch_no'],
                    'pull_good_qty': item['available_qty'],
                    'pull_bad_qty': item['bad_qty'],
                    'object': 'OutwareInboundSku',
                })
            dict_params = DictObject().fresh_form_data(params)
        except Exception, exc:
            logging.error('响应数据格式不对: %s' % str(exc), exc_info=True)
            return Response({'code': 2, 'info': '响应数据格式不对: %s' % str(exc)})

        try:
            resp = pms.update_outware_inbound_by_po_confirm(order_code, order_type, dict_params)
        except Exception, exc:
            logging.error(str(exc), exc_info=True)
            return Response({'code': 0, 'info': str(exc)})

        return Response({'code': not resp['success'] and 1 or 0, 'info': resp.get('message','')})

    @list_route(methods=['POST'])
    def order_state(self, request, *args, **kwargs):
        """
        Waving(25, "波次进行中"),
        WaveCompleted(26, "开始拣货"),
        PickedCompleted(30, "拣货完成"),
        Sorting(35, "开始分拣"),
        SortedCompleted(40, "分拣完成"),
        Packing(50, "开始包装"),
        PackedCompleted(60, "包装完成"),
        Loading(65, "装车中"),
        ManifestCompleted(70, "装车完成"),
        Sended(80, "已发货"),
        received(85, "收货确认"),
        """
        req_data = request.POST.dict()
        logger.info({
            'action': 'fengchao_orderstate',
            'action_time': datetime.datetime.now(),
            'data': req_data,
        })
        if not self.verify_request(req_data):
            return Response({'code': 1, 'info': '签名无效'})

        try:
            data = json.loads(req_data['data'])
        except Exception, exc:
            logging.error('响应数据格式不对: %s' % str(exc), exc_info=True)
            return Response({'code': 1, 'info': '响应数据格式不对: %s' % str(exc)})

        try:
            oms.update_outware_order_by_order_state_change(data['order_number'], data['status'])
        except Exception, exc:
            logging.error(str(exc), exc_info=True)
            return Response({'code': 0, 'info': str(exc)})

        return Response({'code': 0, 'info': 'success'})

    @list_route(methods=['POST'])
    def order_goodlack(self, request, *args, **kwargs):
        """
        return :
        {
            'order_number': xxxx,
            'lack_goods': [
                {
                    'sku_code': xxx,
                    'sku_name': xxx,
                    'lack_qty': 1
                }
            ]
        }
        """
        req_data = request.POST.dict()
        logger.info({
            'action': 'fengchao_goodlack',
            'action_time': datetime.datetime.now(),
            'data': req_data,
        })
        if not self.verify_request(req_data):
            return Response({'code': 1, 'info': '签名无效'})

        try:
            data = json.loads(req_data['data'])
            params = {
                'order_code': data['order_number'],
                'order_type': constants.ORDER_LACKGOOD['code'],
                'lack_goods': [],
                'object': 'OutWareLackOrder'
            }
            for good in data['lack_goods']:
                good.update({'object': 'OutWareLackOrderGood'})
                params['lack_goods'].append(good)

            dict_params = DictObject().fresh_form_data(params)
        except Exception, exc:
            logging.error('响应数据格式不对: %s' % str(exc), exc_info=True)
            return Response({'code': 2, 'info': '响应数据格式不对: %s' % str(exc)})

        try:
            oms.update_outware_order_by_order_goodlacks(data['order_number'], dict_params)
        except Exception, exc:
            logging.error(str(exc), exc_info=True)
            return Response({'code': 0, 'info': str(exc)})

        return Response({'code': 0, 'info': 'success'})

    @list_route(methods=['POST'])
    def order_delivery(self, request, *args, **kwargs):
        req_data = request.POST.dict()
        logger.info({
            'action': 'fengchao_orderdelivery',
            'action_time': datetime.datetime.now(),
            'data': req_data,
        })
        if not self.verify_request(req_data):
            return Response({'code': 1, 'info': '签名无效'})

        try:
            data = json.loads(req_data['data'])
            order_code = data['order_code']

            order_type = (constants.ORDER_RETURN['code'], constants.ORDER_SALE['code'])\
                [data['order_type'].lower() == 'user_pack' and 1 or 0]

            params = {
                'order_code': order_code,
                'order_type': order_type,
                'packages': [],
                'object': 'OutwareObject',
            }
            for package in data['packages']:
                package_params = {
                    'store_code': package['whse_code'],
                    'logistics_no': package['logistics_no'],
                    'carrier_code': package['carrier_code'],
                    'package_items': [],
                    'object': 'OutwarePackage',
                }
                params['packages'].append(package_params)
                for item in package['package_items']:
                    package_params['package_items'].append({
                        'sku_code': item['sku_id'],
                        'batch_no': item.get('batch_no',''),
                        'sku_qty': item['send_qty'],
                        'object': 'OutwarePackageSku',
                    })
            dict_params = DictObject().fresh_form_data(params)
        except Exception, exc:
            logging.error('响应数据格式不对: %s'%str(exc), exc_info=True)
            return Response({'code': 2, 'info': '响应数据格式不对: %s'%str(exc)})

        try:
            resp = oms.update_outware_order_by_order_delivery(order_code, order_type, dict_params)
        except Exception, exc:
            logging.error(str(exc), exc_info=True)
            return Response({'code': 0, 'info': str(exc)})

        return Response({'code': not resp['success'] and 1 or 0, 'info': resp['message']})





