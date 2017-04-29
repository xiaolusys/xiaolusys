# coding: utf8
from __future__ import absolute_import, unicode_literals

import hashlib
import json
import requests
import datetime

from ... import constants
from django.conf import settings
from shopback.outware.models.base import log_ware_action

from .exceptions import FengchaoApiException

import logging
logger = logging.getLogger(__name__)

FENGCHAO_SLYC_VENDOR_CODE  = settings.FENGCHAO_SLYC_VENDOR_CODE
FENGCHAO_SLYC_CHANNEL_CODE = settings.FENGCHAO_SLYC_CHANNEL_CODE # 十里洋场的订单channel
FENGCHAO_DEFAULT_CHANNEL_CODE = settings.FENGCHAO_DEFAULT_CHANNEL_CODE

FENGCHAO_API_GETWAY = settings.FENGCHAO_API_GETWAY
FENGCHAO_APPID = settings.FENGCHAO_APPID
FENGCHAO_SECRET = settings.FENGCHAO_SECRET

def sign_string(string, secret):
    return hashlib.md5(str(string + secret)).hexdigest().upper()

def request_getway(data, notify_type, account):
    logger.info({
        'action': 'fengchao_notify_type_%s'%notify_type,
        'action_time': datetime.datetime.now(),
        'data': data,
    })

    data_str = str(json.dumps(data, ensure_ascii=False, encoding='utf8'))
    req_params = {
        'app_id': FENGCHAO_APPID,
        'notify_type': notify_type,
        'sign_type': 'md5',
        'sign': sign_string(data_str, FENGCHAO_SECRET),
        'data': data_str,
    }

    resp = requests.post(FENGCHAO_API_GETWAY, data=req_params, verify=False)
    if not resp.status_code == 200:
        raise FengchaoApiException('蜂巢api错误: %s'%resp.text)

    content = json.loads(resp.text)
    if not content.get('success'):
        raise FengchaoApiException('蜂巢api错误: %s' % content.get('error_msg'))

    return content


# @action_decorator(constants.ACTION_ORDER_CHANNEL_CREATE['code'])
def create_fengchao_order_channel(channel_client_id, channel_name, channel_type, channel_id):
    """　创建蜂巢订单来源渠道 """
    # TODO 该方法已失效，channelid 通过两个商议来对接

    from ..models import FengchaoOrderChannel
    from shopback.outware.models import OutwareAccount
    ware_account = OutwareAccount.get_fengchao_account()

    channel, state = FengchaoOrderChannel.objects.get_or_create(
        channel_id=channel_id
    )
    if state:
        channel.channel_name = channel_name
        channel.channel_type = channel_type
        channel.channel_client_id = channel_client_id
        channel.save()

    params = {
        'channel_id': channel_id,
        'channel_name': channel_name,
        'channel_type': channel_type,
        'channel_client_id': channel_client_id,
    }

    try:
        request_getway(params, constants.ACTION_ORDER_CHANNEL_CREATE['code'], ware_account)
    except Exception, exc:
        logger.error(str(exc), exc_info=True)
        return {'success': False, 'object': channel, 'message': str(exc)}

    channel.status = True
    channel.save()

    return {'success': True, 'object': channel, 'message': '' }


def get_skustock_by_qureyparams(sku_codes, vendor_code=None):
    """　创建蜂巢订单来源渠道 """
    if not sku_codes:
        return []

    from shopback.outware.models import OutwareAccount
    ware_account = OutwareAccount.get_fengchao_account()

    sku_querys = {'skus':[]}
    if vendor_code:
        sku_querys['vendor_code'] = vendor_code

    for sku_code in sku_codes:
        sku_querys['skus'].append({
            'sku_id': sku_code,
            'sku_type': 20
        })

    action_code = constants.ACTION_SKU_STOCK_PULL['code']

    try:
        resp = request_getway(sku_querys, action_code, ware_account)
    except Exception, exc:
        logger.error(str(exc), exc_info=True)
        log_ware_action(ware_account, action_code, state_code=constants.ERROR, message=str(exc))
        return []

    return resp['inventory']


def get_channelid_by_vendor_codes(vendor_codes):
    # vendor_codes: 根据vendor_code　返回对应的channel字典
    channel_maps = {}
    for vendor_code in vendor_codes:
        channel_maps[vendor_code] = FENGCHAO_DEFAULT_CHANNEL_CODE
    return channel_maps

def if_is_slyc_vendor(vendor_codes):
    for vendor_code in vendor_codes:
        if not all(vendor_code.upper().startswith(i) for i in ['SLYC', 'FENGHCAO']):
            return False
    return True

def get_carrier_code_by_logistics_company_code(logistic_company_code):
    """ 系统快递编码对应蜂巢快递编码,返回空字符串表示不支持该快递 """
    maps = {
        'OTHER': 'OTHER',
        'EMS': 'EMS',
        'ZTO': 'ZTO',
        'SF': 'SF',
        'STO': 'STO',
        'CBWL': 'CBWL',
        'ZKWL': 'ZKWL',
        'TTKDEX': 'TTK',
        'POSTB': 'POSTB',
        'YUNDA_QR': 'YUNDA',
        'YTO': 'YTO',
    }
    return maps.get(logistic_company_code,'')