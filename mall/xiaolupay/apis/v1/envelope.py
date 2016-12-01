# coding:utf8
"""
参考: https://www.pingxx.com/api#red-envelopes-红包
"""
import requests
import hashlib
from django.template import Context, Template
from django.conf import settings
from lxml import etree
from mall.xiaolupay.models.weixin_red_envelope import WeixinRedEnvelope


TEMPLATE = """
<xml>
{% for k, v in params.items %}
<{{k}}><![CDATA[{{v}}]]></{{k}}>
{% endfor %}
</xml>
"""


class WeixinRedEnvelopAPI(object):

    ssl_key = settings.WEIXIN_PAY_SSL_KEY
    ssl_cert = settings.WEIXIN_PAY_SSL_CERT
    nonce_str = '50780e0cca98c8c8e814883e5caa672e'
    wx_account = None

    def __init__(self):
        pass

    def _request(self, url, params):
        data = self._dict_to_xml(params)
        resp = requests.post(url, data=data, cert=(self.ssl_cert, self.ssl_key), verify=False)
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

    def createEnvelop(self, envelope):
        """
        发送红包
        """
        url = 'https://api.mch.weixin.qq.com/mmpaymkttransfers/sendredpack'
        params = {
            'mch_billno': envelope.mch_billno,
            'mch_id': envelope.mch_id,
            'wxappid': envelope.wxappid,
            'send_name': envelope.send_name,
            're_openid': envelope.openid,
            'total_amount': envelope.total_amount,
            'total_num': envelope.total_num,
            'wishing': envelope.wishing,
            'client_ip': envelope.client_ip,
            'act_name': envelope.act_name,
            'remark': envelope.remark,
            'nonce_str': self.nonce_str
        }
        self.set_wx_account(envelope.wxappid)
        result = self._request(url, params)
        return envelope.update_sync_result(result)

    def createGroupEnvelop(self):
        """
        发送裂变红包
        """
        pass

    def queryEnvelope(self, envelope):
        """
        查询
        """
        url = 'https://api.mch.weixin.qq.com/mmpaymkttransfers/gethbinfo'
        params = {
            'mch_billno': envelope.mch_billno,
            'mch_id': envelope.mch_id,
            'appid': envelope.wxappid,
            'bill_type': 'MCHT',
            'nonce_str': self.nonce_str
        }
        self.set_wx_account(envelope.wxappid)
        result = self._request(url, params)
        return envelope.sync_envelope_info(result)


def create(order_no, amount, subject, body, recipient, remark):
    """
    创建微信红包
    """
    from mall.xiaolupay.tasks.tasks_envelope import task_sent_weixin_red_envelope
    from shopapp.weixin.models import WeiXinAccount

    # recipient = 'our5huD8xO6QY-lJc1DTrqRut3us'

    envelope = WeixinRedEnvelope.objects.filter(mch_billno=order_no).first()
    if envelope:
        return envelope

    wx_account = WeiXinAccount.objects.get(app_id=settings.WX_PUB_APPID)

    envelope = WeixinRedEnvelope()
    envelope.mch_billno = order_no
    envelope.mch_id = wx_account.partner_id
    envelope.wxappid = wx_account.app_id
    envelope.send_name = u'小鹿美美'
    envelope.openid = recipient
    envelope.total_amount = amount
    envelope.total_num = 1
    envelope.wishing = body
    envelope.client_ip = '127.0.0.1'
    envelope.act_name = subject
    envelope.remark = remark
    envelope.save()

    try:
        task_sent_weixin_red_envelope.delay(envelope.id)
    except Exception:
        pass

    return envelope


def retrieve(envelop_id):
    envelope = WeixinRedEnvelope.objects.filter(id=envelop_id).first()
    return envelope
