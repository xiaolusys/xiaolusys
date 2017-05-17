# coding:utf8
"""
参考: https://pay.weixin.qq.com/wiki/doc/api/tools/mch_pay.php?chapter=14_2
"""
from __future__ import absolute_import, unicode_literals

import requests
import hashlib
from django.template import Context, Template
from django.conf import settings
from lxml import etree
from flashsale.xiaolupay.models.weixin_transfers import WeixinTransfers


TEMPLATE = """
<xml>
{% for k, v in params.items %}
<{{k}}><![CDATA[{{v}}]]></{{k}}>
{% endfor %}
</xml>
"""


class WeixinTransfersAPI(object):

    ssl_key = settings.WX_PUB_KEY_PEM_PATH
    ssl_cert = settings.WX_PUB_CERT_PEM_PATH
    nonce_str = '50780e0cca98c8c8e814883e5caa672e'
    wx_account = None
    request_body = ''
    response_body = ''

    def __init__(self):
        pass

    def _request(self, url, params):
        data = self._dict_to_xml(params)
        self.request_body = data
        resp = requests.post(url, data=data, cert=(self.ssl_cert, self.ssl_key), verify=False)
        self.response_body = resp.content
        result = self._xml_to_dict(resp.content)
        return result

    def _sign(self, params):
        key = self.wx_account.partner_key
        items = sorted(params.items())
        string_a = '&'.join(['%s=%s' % (k, v) for (k, v) in items])
        string_temp = string_a + '&key=%s' % key
        sign_str = hashlib.md5(string_temp.encode('utf8')).hexdigest().upper()
        return sign_str

    def _dict_to_xml(self, params):
        params['sign'] = self._sign(params)
        template = Template(TEMPLATE)
        context = Context({'params': params})
        xml = template.render(context)
        return xml.encode('utf8')

    def _xml_to_dict(self, xml):
        """
        TODO: 没有区分数组
        例如：裂变红包时 hblist 是一个数组，这个函数只会取一个
        """
        data = {}
        root = etree.fromstring(xml)
        for child in root.getchildren():
            if child.getchildren():
                data[child.tag] = self._xml_to_dict(etree.tostring(child))
            else:
                data[child.tag] = child.text
        return data

    def set_wx_account(self, app_id):
        from shopapp.weixin.models import WeiXinAccount

        wx_account = WeiXinAccount.objects.get(app_id=app_id)
        self.wx_account = wx_account

    def transfer(self, openid, name, amount, desc, trade_id):
        self.set_wx_account(app_id=settings.WX_PUB_APPID)

        url = 'https://api.mch.weixin.qq.com/mmpaymkttransfers/promotion/transfers'
        params = {
            'mch_appid': self.wx_account.app_id,
            'mchid': self.wx_account.partner_id,
            'nonce_str': self.nonce_str,
            'partner_trade_no': trade_id,
            'openid': openid,
            'check_name': 'FORCE_CHECK',
            're_user_name': name,
            'amount': amount,
            'desc': desc,
            'spbill_create_ip': '127.0.0.1'
        }
        res = self._request(url, params)
        return res


def transfer(openid, name, amount, desc, trade_id):
    """
    微信企业转账

    params:
    - custoemr_id
    - name 用户真实姓名
    - amount 金额(分)
    - desc
    - trade_id 交易ID(自定义,唯一)
    """

    api = WeixinTransfersAPI()
    res = api.transfer(openid, name, amount, desc, trade_id)

    return_code = res['return_code']
    return_msg = res.get('return_msg', '')
    result_code = res.get('result_code', '')
    err_code = res.get('err_code', '')
    err_code_des = res.get('err_code_des', '')
    payment_no = res.get('payment_no', '')

    if return_code == 'FAIL':
        raise Exception(return_msg)

    wt = WeixinTransfers()
    wt.mch_id = api.wx_account.partner_id
    wt.wxappid = api.wx_account.app_id
    wt.mch_billno = trade_id
    wt.payment_no = payment_no
    wt.openid = openid
    wt.name = name or ''
    wt.amount = amount
    wt.desc = desc
    wt.return_code = return_code
    wt.return_msg = return_msg
    wt.result_code = result_code
    wt.err_code = err_code
    wt.err_code_des = err_code_des
    wt.request_body = api.request_body
    wt.response_body = api.response_body
    wt.save()

    success = True if result_code == 'SUCCESS' else False
    return success