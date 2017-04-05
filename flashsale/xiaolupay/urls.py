# coding=utf-8
from __future__ import absolute_import, unicode_literals

import json
from django.conf.urls import include, url
from .views.notify import pay_channel_notify


urlpatterns = [
     url(r'^(?P<channel>\w+)/', pay_channel_notify, name='pay_channel_notify')
]