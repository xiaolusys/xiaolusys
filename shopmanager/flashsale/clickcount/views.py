# coding=utf-8
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from .models import ClickCount
from shopmanager.flashsale.xiaolumm.models import Clicks, XiaoluMama
import datetime
import json
from django.forms import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import User
