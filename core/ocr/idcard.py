# coding: utf8
from __future__ import absolute_import, unicode_literals

import requests
import json

from django.conf import settings

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
