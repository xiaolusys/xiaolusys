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


def sign(params):
    key = 't5UXHfwR7QEv2jMLFuZm8DdqnAT0ON9a'
    items = sorted(params.items())
    string_a = '&'.join(['%s=%s' % (k, v) for (k, v) in items])
    string_temp = string_a + '&key=%s' % key
    sign_str = hashlib.md5(string_temp.encode('utf8')).hexdigest().upper()
    return sign_str


def dict_to_xml(params):
    params['sign'] = sign(params)
    template = Template(TEMPLATE)
    context = Context({'params': params})
    xml = template.render(context)
    return xml.encode('utf8')


def xml_to_dict(xml):
    """
    TODO: 没有区分数组
    例如：裂变红包时 hblist 是一个数组，这个函数只会取一个
    """
    data = {}
    root = etree.fromstring(xml)
    for child in root.getchildren():
        if child.getchildren():
            data[child.tag] = xml_to_dict(etree.tostring(child))
        else:
            data[child.tag] = child.text
    return data


class WeixinRedEnvelopAPI(object):

    mch_billno = ''
    mch_id = '1236482102'  # 商户号
    wxappid = 'wx3f91056a2928ad2d'  # 公众账号appid
    send_name = u'小鹿美美'  # 商户名称
    re_openid = ''
    total_amount = ''
    total_num = ''
    wishing = ''
    client_ip = ''
    act_name = ''
    remark = ''
    nonce_str = ''

    ssl_key = '/home/aladdin/doc/weixin-pay-wap/apiclient_key.pem'
    ssl_cert = '/home/aladdin/doc/weixin-pay-wap/apiclient_cert.pem'

    def __init__(self):
        pass

    def _request(self, url, params):
        data = dict_to_xml(params)
        resp = requests.post(url, data=data, cert=(self.ssl_cert, self.ssl_key), verify=False)
        result = xml_to_dict(resp.content)
        import simplejson
        print simplejson.dumps(result, indent=2)
        return result

    def createEnvelop(self, envelope):
        """
        发送红包
        """
        # openid = 'our5huD8xO6QY-lJc1DTrqRut3us'
        nonce_str = '50780e0cca98c8c8e814883e5caa672e'

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
            'nonce_str': nonce_str
        }
        result = self._request(url, params)
        return envelope.update_sync_result(result)

    def createGroupEnvelop(self):
        """
        发送裂变红包
        """
        url = 'https://api.mch.weixin.qq.com/mmpaymkttransfers/sendgroupredpack'
        params = {
            'mch_billno': 'testEnvelop002',
            'mch_id': self.mch_id,
            'wxappid': self.wxappid,
            'send_name': self.send_name,
            're_openid': 'our5huD8xO6QY-lJc1DTrqRut3us',
            'total_amount': '200',
            'amt_type': 'ALL_RAND',
            'total_num': '5',
            'wishing': u'祝福语：赏你的',
            'act_name': u'活动名称：任性活动',
            'remark': u'备注信息',
            # 'scene_id': '',
            'nonce_str': '50780e0cca98c8c8e814883e5caa672e',
            # 'risk_info': '',
            # 'consume_mch_id': '',
        }
        return self._request(url, params)

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
            'nonce_str': '50780e0cca98c8c8e814883e5caa672e'
        }

        result = self._request(url, params)
        return envelope.sync_envelope_info(result)


def create(order_no, amount, subject, body, recipient, remark):
    """
    创建微信红包
    """
    from mall.xiaolupay.tasks.tasks_envelope import task_sent_weixin_red_envelope

    envelope = WeixinRedEnvelope.objects.filter(mch_billno=order_no).first()
    if envelope:
        return envelope

    envelope = WeixinRedEnvelope()
    envelope.mch_billno = order_no
    envelope.mch_id = settings.WX_PAY_MCH_ID
    envelope.wxappid = settings.WXPAY_APPID
    envelope.send_name = u'小鹿美美'
    envelope.openid = recipient
    envelope.total_amount = amount
    envelope.total_num = 1
    envelope.wishing = body
    envelope.client_ip = '192.168.1.57'
    envelope.act_name = subject
    envelope.remark = remark
    envelope.save()

    try:
        # task_sent_weixin_red_envelope.delay(envelope.id)
        task_sent_weixin_red_envelope(envelope.id)
    except Exception:
        pass

    return envelope


def retrieve(envelop_id):
    envelope = WeixinRedEnvelope.objects.filter(id=envelop_id).first()
    return envelope
