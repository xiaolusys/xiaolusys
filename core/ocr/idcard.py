# coding: utf8
from __future__ import absolute_import, unicode_literals

import logging

import requests
import json
import simplejson

from django.conf import settings

logger = logging.getLogger(__name__)

host_url = settings.IDCARD_OCR_URL
appcode = settings.ALIYUN_APPCODE

def verify(card_no):
    verify_byte = '10X98765432'[sum(map(lambda x: int(x[0]) * x[1], zip(card_no[0:17], [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]) )) % 11]
    return len(card_no) > 17 and verify_byte == card_no[-1]

def identify(side, image_base64):
    post_data = json.dumps({
        "inputs": [
            {
                "image": {
                    "dataType": 50,
                    "dataValue": image_base64
                },
                "configure": {
                    "dataType": 50,
                    "dataValue": "{\"side\":\"%s\"}"%side
                }
            }
        ]
    })

    headers = {
        'Authorization': 'APPCODE ' + appcode,
        'Content-Type': 'application/json; charset=UTF-8'
    }
    r = requests.post(host_url, headers=headers, data=post_data, verify=False)
    if r.status_code >= 400:
        raise Exception(r.text)

    resp_content = json.loads(r.text)
    return json.loads(resp_content['outputs'][0]['outputValue']['dataValue'])


def check_name(card_no, name):
    """
    身份证实名验证

    params:
    - card_no <str> 身份证号
    - name <str> 姓名

    return:
    <boolean>

    接口文档:
    https://market.aliyun.com/products/57000002/cmapi012507.html?spm=5176.8278668.629621.1.El3WFm#sku=yuncode650700000
    """
    url = 'http://aliyun.id98.cn/idcard'
    params = {
        'cardno': card_no,
        'name': name
    }
    headers = {
        'Authorization': 'APPCODE {}'.format(appcode)
    }
    resp = requests.get(url, params=params, headers=headers)
    print resp.content
    code = simplejson.loads(resp.content)['code']

    if code == 1:
        return True

    if code == 20:
        logger.error(u'第三方接口报错: 身份证中心维护中')

    return False
