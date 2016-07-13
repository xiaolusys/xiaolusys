# coding: utf-8
from django import forms
from core.forms import BaseForm
from django.core.validators import RegexValidator


class GroupFansForm(BaseForm):
    group_id = forms.IntegerField(error_messages=u'必须提供微信群ID')