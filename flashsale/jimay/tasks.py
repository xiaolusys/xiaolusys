# coding: utf8
from __future__ import absolute_import, unicode_literals

import re
import datetime
import json

from shopmanager import celery_app as app
from django.conf import settings

from flashsale.jimay.models import JimayAgent

import logging
logger = logging.getLogger(__name__)

@app.task
def task_generate_jimay_agent_certification(agent_id):
    """ 创建己美医学特约代理授权证书 """
    agent = JimayAgent.objects.get(id=agent_id)

    from shopapp.weixin.models.base import WeixinQRcodeTemplate
    from shopapp.weixin.utils import generate_colorful_qrcode
    from core.upload.upload import upload_public_to_remote, generate_public_url

    cert_qr = WeixinQRcodeTemplate.get_agent_cert_templates().first()
    if not cert_qr:
        logger.error('己美医学授权证书无法生成，请先去[微信二维码模板]创建证书模板: agent_id=%s' % agent_id)
        return ''

    params = json.loads(cert_qr.params)
    params['texts'][0]['content'] = agent.name
    params['texts'][1]['content'] = agent.idcard_no
    params['texts'][2]['content'] = agent.weixin

    qrcode_io = generate_colorful_qrcode(params)
    filename = agent.gen_certification_filename()

    upload_public_to_remote(filename, qrcode_io)
    preview_url = generate_public_url(filename)

    agent.set_certification(preview_url)

    return preview_url




