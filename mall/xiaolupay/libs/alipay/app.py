# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import rsa
import base64
import os
import json
import datetime
import requests
from urllib import quote

from .exceptions import AliPayAPIError, AliPayAPIResponseError
from .conf import AlipayConf
from .utils import serial_dict, encode_dict


def read_file(file_path):
    with open(file_path, "r") as f:
        return f.read()

class AliPay(object):

    _encode_charset = 'utf-8'
    _sign_type = 'RSA'
    _getway_url = AlipayConf.GATEWAY_URL

    def __init__(self):
        private_pem = read_file(AlipayConf.PRIVATE_KEY_PATH)
        self._private_rsa_key = rsa.PrivateKey.load_pkcs1(private_pem)


    def _default_params(self):
        return {
            'app_id': AlipayConf.APP_ID,
            'charset': self._encode_charset,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'version': '1.0',
            'format': 'JSON',
            'sign_type': self._sign_type,
        }

    def _build_request_url(self, head_params, biz_params):
        biz_content = json.dumps(biz_params, ensure_ascii=False) #,separators=(',', ':')
        params = self._default_params()
        params.update(head_params)
        params.update(biz_content=biz_content)
        params = encode_dict(params)

        sign_content = serial_dict(params)
        params.update(sign=self._create_sign(sign_content))

        serial_content = serial_dict(params, value_quote=True).encode(self._encode_charset)
        return serial_content

    def _create_sign(self, content):
        content = content.encode(self._encode_charset)
        sign = rsa.sign(content, self._private_rsa_key, "SHA-1")
        sign = base64.encodestring(sign).replace("\n", "")
        return sign


    def process_alipay_response(self, resp_text):

        resp_json = json.loads(resp_text)
        for k, v in resp_json.iteritems():
            if k.endswith('_response'):
                if 'sub_code' in v and 'sub_msg' in v:
                    raise AliPayAPIError(fail_code=v['sub_code'], fail_msg=v['sub_msg'])
                return v

        #TODO 参数进行签名校验

        raise AliPayAPIResponseError(resp_text)

    def _send_request(self, request_url):
        resp = requests.get('%s?%s'%(self._getway_url, request_url), verify=AlipayConf.VERIFY_CERTIFICATE)
        return self.process_alipay_response(resp.text)

    def create_trade_app_pay_url(self, out_trade_no, total_amount, subject, body=''):
        head_params = {
            'method': 'alipay.trade.app.pay',
            'notify_url': AlipayConf.NOTIFY_URL,
        }
        biz_params = {
            'out_trade_no': out_trade_no,
            'total_amount': total_amount,
            'subject': subject,
            'body': body,
            'timeout_express': '2h',
            'product_code': 'QUICK_MSECURITY_PAY',
        }
        return self._build_request_url(head_params, biz_params)

    def trade_wap_pay(self, out_trade_no, total_amount, subject, body=''):
        """ deprecated """
        head_params = {
            'method': 'alipay.trade.wap.pay',
            'notify_url': AlipayConf.NOTIFY_URL,
        }
        biz_params = {
            'out_trade_no': out_trade_no,
            'total_amount': total_amount,
            'subject': subject,
            'body': body,
            'product_code': 'QUICK_WAP_PAY',
        }
        return self._build_request_url(head_params, biz_params)

    def trade_query(self, out_trade_no):
        """
        {
          "trade_no": "2016112821001004280288507138",
          "code": "10000",
          "buyer_user_id": "xxx",
          "open_id": "xxx",
          "buyer_logon_id": "215***@qq.com",
          "send_pay_date": "2016-11-28 09:48:38",
          "receipt_amount": "0.00",
          "out_trade_no": "xd161128583b8cc7889ed",
          "buyer_pay_amount": "0.00",
          "invoice_amount": "0.00",
          "msg": "Success",
          "point_amount": "0.00",
          "trade_status": "TRADE_SUCCESS",
          "total_amount": "62.60"
        }
        """
        head_params = {
            'method': 'alipay.trade.query',
        }
        biz_params = {
            'out_trade_no': out_trade_no,
        }
        query_url = self._build_request_url(head_params, biz_params)
        return self._send_request(query_url)

    def trade_refund(self, out_trade_no, refund_amount, refund_reason='', out_request_no=''):
        """
        {
            "buyer_logon_id":"159****5620",
            "buyer_user_id":"xxx",
            "code":"10000",
            "fund_change":"Y",
            "gmt_refund_pay":"2014-11-27 15:45:57",
            "msg":"Success",
            "open_id":"xxx",
            "out_trade_no":"6823789339978248",
            "refund_detail_item_list":[{
                "amount":10,
                "fund_channel":"ALIPAYACCOUNT",
                "real_amount":11.21
            }],
            "refund_fee":88.88,
            "send_back_fee":"1.8",
            "store_name":"望湘园联洋店",
            "trade_no":"支付宝交易号"
        }
        """
        head_params = {
            'method': 'alipay.trade.refund',
        }
        biz_params = {
            'out_trade_no': out_trade_no,
            'refund_amount': refund_amount,
            'refund_reason': refund_reason,
            'out_request_no': out_request_no,
        }
        query_url = self._build_request_url(head_params, biz_params)
        return self._send_request(query_url)

    def trade_fastpay_refund_query(self, out_trade_no, out_request_no):
        head_params = {
            'method': 'alipay.trade.fastpay.refund.query',
        }
        biz_params = {
            'out_trade_no': out_trade_no,
            'out_request_no': out_request_no,
        }
        query_url = self._build_request_url(head_params, biz_params)
        return self._send_request(query_url)

    def check_notify_sign(self, notify_params):
        """
        按照字母顺序排序，然后使用阿里云的公匙验证。
        """

        public_pem = read_file(AlipayConf.PUBLIC_KEY_PATH)
        _public_rsa_key_ali = rsa.PublicKey.load_pkcs1_openssl_pem(public_pem)

        params = notify_params.copy()
        sign = params.pop('sign')
        params.pop('sign_type', 'RSA')

        param_list = sorted(params, key=lambda d: d[0], reverse=False)
        content = "&".join("{}={}".format(k, v) for k, v in param_list)
        content = content.encode("utf-8")
        try:
            sign = base64.decodestring(sign)
            rsa.verify(content, sign, _public_rsa_key_ali)
            return True
        except Exception, e:
            return False


def notify_sign_value(request, content, key):
    if key in request.POST:
        value = request.POST[key]
        print "key: ", key, "value: ", value
        return "&%s=%s"%(key, value)
    else:
        return ""


