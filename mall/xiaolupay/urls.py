# coding=utf-8
from __future__ import absolute_import, unicode_literals

import json
from django.conf.urls import include, url
from .views.notify import alipay_notify, wxpay_notify


urlpatterns = [
     url(r'^alipay/', alipay_notify, name='alipay_notify'),
     url(r'^wxpay/', wxpay_notify, name='wxpay_notify'),
]