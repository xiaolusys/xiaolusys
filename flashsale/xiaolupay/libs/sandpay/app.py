# coding: utf8
from __future__ import absolute_import, unicode_literals

import re
import logging
import datetime
import json
import urllib
import requests

from .serializers import SandpayApiJSONEncoder, repair_brokenjson
from .conf import SandpayConf
from . import exceptions
from . import cipher

logger = logging.getLogger(__name__)

class Sandpay(object):

    def __init__(self,
                 access_type,
                 mer_id,
                 pl_id='',
                 aes_ecb_sercret='',
                 rsa_private_key_path='',
                 rsa_public_key_path='',
            ):

        self.access_type = access_type
        self.mer_id   = mer_id
        self.pl_id    = pl_id
        self.aes_ecb_sercret  = aes_ecb_sercret or SandpayConf.gen_aes_secret()
        self.rsa_private_path = rsa_private_key_path or SandpayConf.SANDPAY_RSA_KEY_PATH
        self.rsa_public_path  = rsa_public_key_path or SandpayConf.SANDPAY_RSA_CERT_PATH

        if access_type == SandpayConf.AC_PLATFORM and not self.pl_id:
            raise ValueError('need valid pl_id!')

    def request_getway(self, req_uri, req_data):
        req_url = '{}{}'.format(SandpayConf.SANDPAY_API_GETWAY, req_uri)
        resp = requests.post(req_url, data=req_data)

        resp_dict = self.decrypt_message(resp.text)
        logger.debug({
            'action': 'sandpay_request',
            'action_time': datetime.datetime.now(),
            'request_url': req_url,
            'request': req_data,
            'response': resp_dict,
        })
        resp_code = resp_dict.get('respCode')
        resp_desc = '%s: %s' % (resp_dict.get('respDesc'), resp_code)
        if resp_code == '0000':
            return resp_dict
        elif resp_code.startswith('00'):
            raise exceptions.SandpaySystemError(resp_desc)

        elif resp_code.startswith('10'):
            raise exceptions.SandpaySystemError(resp_desc)

        elif resp_code.startswith('20'):
            raise exceptions.SandpaySystemError(resp_desc)

        elif resp_code.startswith('30'):
            raise exceptions.SandpaySystemError(resp_desc)

        else:
            raise exceptions.SandpayException(resp.text)

    @property
    def common_protocal_data(self):
        # 请求协议共同数据
        c_data = {
            'accessType': self.access_type,
            'merId': self.mer_id,
        }
        if self.access_type == SandpayConf.AC_PLATFORM:
            c_data['plId'] = self.pl_id

        return c_data

    @property
    def common_service_data(self):
        # 请求业务共同数据
        return {
            'version': '01'
        }

    def encrypt_message(self, trans_code, req_json):
        protocal = self.common_protocal_data
        protocal['transCode'] = trans_code
        logger.debug({
            'action': 'sandpay_encryp_message',
            'protocal': protocal,
            'data': req_json,
        })
        req_json_str = json.dumps(req_json, cls=SandpayApiJSONEncoder, encoding='utf8')

        protocal['encryptData'] = cipher.AESCipher.ecb_encrypt(req_json_str, self.aes_ecb_sercret)
        protocal['encryptKey']  = cipher.RSACipher.encrypt(self.aes_ecb_sercret, self.rsa_public_path)
        protocal['sign'] = cipher.RSACipher.sign(req_json_str, self.rsa_private_path, 'SHA-1')

        return protocal

    def decrypt_message(self, encrypt_resp):
        encry_dict = dict([e.split('=') for e in encrypt_resp.split('&')])
        decrypt_aes_key = cipher.RSACipher.decrypt(urllib.unquote(encry_dict['encryptKey']), self.rsa_private_path)
        decrypt_data    = cipher.AESCipher.ecb_decrypt(urllib.unquote(encry_dict['encryptData']), decrypt_aes_key)
        decrypt_data    = decrypt_data.decode('utf-8')
        decrypt_data    = decrypt_data[:decrypt_data.rfind('}') + 1]
        return json.loads(decrypt_data, strict=False)

    def agent_pay(self, **kwargs):
        """ DEFAULT product_id: 00000004 """

        srv_data = self.common_service_data
        srv_data.update(kwargs)

        protocal_data = self.encrypt_message('RTPM', srv_data)
        resp_data = self.request_getway('/agentpay', protocal_data)
        return resp_data

    def query_order(self,
                    order_code,
                    tran_time,
                    product_attr=SandpayConf.PRO_TRANS2PRI):
        """ search for sand code """
        srv_data = self.common_service_data.copy()
        srv_data.update({
            'productId': product_attr[0],
            'tranTime': tran_time,
            'orderCode': order_code,
        })

        protocal_data = self.encrypt_message('ODQU', srv_data)
        resp_data = self.request_getway('/queryorder', protocal_data)
        return resp_data


