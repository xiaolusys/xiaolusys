# coding: utf8
from __future__ import absolute_import, unicode_literals

from shopmanager import celery_app as app
from ..utils import generate_colorful_qrcode

@app.task(ignore_result=False)
def task_generate_colorful_qrcode(params):
    return generate_colorful_qrcode(params)