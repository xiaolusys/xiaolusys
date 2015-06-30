#-*- coding:utf-8 -*-

import json
from django.http import HttpResponse,Http404
from django.shortcuts import redirect,render_to_response
from django.views.generic import View
from django.template import RequestContext
from django.contrib.auth.models import User
from django.db.models import Sum

from shopapp.weixin.views import get_user_openid,valid_openid
from shopapp.weixin.models import WXOrder
from shopapp.weixin.service import WeixinUserService
from shopback.base import log_action, ADDITION, CHANGE

from rest_framework import generics
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response







