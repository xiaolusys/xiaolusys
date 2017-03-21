# coding: utf8
from __future__ import absolute_import, unicode_literals

from .base import request_getway, create_fengchao_order_channel, get_skustock_by_qureyparams


FENGCHAO_SLYC_VENDOR_CODE  = 'slyc'
FENGCHAO_SLYC_CHANNEL_CODE = 'shiliyangchang' # 十里洋场的订单channel
FENGCHAO_DEFAULT_CHANNEL_CODE = 'xiaolumeimei'

def get_channelid_by_vendor_codes(vendor_codes):
    # vendor_codes: 根据vendor_code　返回对应的channel字典
    channel_maps = {}
    for vendor_code in vendor_codes:
        if vendor_code.lower() == FENGCHAO_SLYC_VENDOR_CODE:
            channel_maps[vendor_code] = FENGCHAO_SLYC_CHANNEL_CODE
        else:
            channel_maps[vendor_code] = FENGCHAO_DEFAULT_CHANNEL_CODE
    return channel_maps


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
        'TTK': 'TTK',
        'TTKDEX': 'TTK',
        'POSTB': 'POSTB',
        'YUNDA': 'YUNDA',
        'YUNDA_QR': 'YUNDA',
        'YTO': 'YTO',
    }
    return maps.get(logistic_company_code,'')