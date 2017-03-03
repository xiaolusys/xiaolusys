# coding: utf8
from __future__ import absolute_import, unicode_literals

import requests
import base64
import json

from django.conf import settings

host_url = settings.IDCARD_OCR_URL
appcode = settings.ALIYUN_APPCODE

def identify(iostream):
    post_data = json.dumps({
        "inputs": [
            {
                "image": {
                    "dataType": 50,
                    "dataValue": base64.encodestring(iostream.read())
                },
                "configure": {
                    "dataType": 50,
                    "dataValue": "{\"side\":\"face\"}"
                }
            }
        ]
    })

    headers = {
        'Authorization': 'APPCODE ' + appcode,
        'Content-Type': 'application/json; charset=UTF-8'
    }
    r = requests.post(host_url, headers=headers, data=post_data, verify=False)
    resp_content = json.loads(r.text)
    return resp_content
