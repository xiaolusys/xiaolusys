# coding: utf-8
from django import forms
from core.forms import BaseForm
from django.core.validators import RegexValidator


class GroupFansForm(BaseForm):
    group_id = forms.CharField(required=True)