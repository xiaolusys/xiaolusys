# coding: utf-8

import sys
from django import forms

from core.forms import BaseForm

from .models import MergeTrade, LogisticsCompany, PackageOrder


class YundaCustomerForm(forms.ModelForm):
    logistics_company = forms.ModelChoiceField(label='物流名称',
                                               queryset=LogisticsCompany.normal_companys())
                                               # choices=())

    class Meta:
        model = MergeTrade
        exclude = ()


class ExchangeTradeForm(forms.Form):
    trade_id = forms.IntegerField(min_value=0, max_value=sys.float_info.max, required=True)
    sellerId = forms.IntegerField(min_value=0, max_value=sys.float_info.max, required=True)

    tid = forms.CharField(max_length=32, required=True)
    trade_type = forms.CharField(max_length=10, required=False)

    buyer_nick = forms.CharField(max_length=64, required=True)
    receiver_name = forms.CharField(max_length=64, required=True)
    receiver_state = forms.CharField(max_length=16, required=True)
    receiver_city = forms.CharField(max_length=16, required=True)
    receiver_district = forms.CharField(max_length=16, required=False)
    receiver_address = forms.CharField(max_length=128, required=True)

    receiver_mobile = forms.CharField(max_length=20, required=False)
    receiver_phone = forms.CharField(max_length=20, required=False)


class StatisticMergeOrderForm(forms.Form):
    df = forms.DateField(input_formats='%Y-%m-%d', required=False)
    dt = forms.DateField(input_formats='%Y-%m-%d', required=False)
    outer_id = forms.CharField(max_length=64, required=False)
    statistic_by = forms.CharField(max_length=64, required=False)


class PayTimeRangeForm(BaseForm):
    pay_time_start = forms.DateField(required=False)
    pay_time_end = forms.DateField(required=False)

    @property
    def json(self):
        if not self.is_valid():
            return {}
        data = {}
        if self.cleaned_attrs.pay_time_start:
            data['pay_time_start'] = self.cleaned_attrs.pay_time_start.strftime('%Y-%m-%d')
        if self.cleaned_attrs.pay_time_end:
            data['pay_time_end'] = self.cleaned_attrs.pay_time_end.strftime('%Y-%m-%d')
        return data


class PackageOrderEditForm(forms.ModelForm):
    user_address_id = forms.CharField(max_length=40, required=False)

    class Meta:
        model = PackageOrder
        fields = ["ware_by", "receiver_mobile", "receiver_name", "receiver_state", "receiver_city",
                              "receiver_district", "receiver_address"]
        # exclude = ['created']
