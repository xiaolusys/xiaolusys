# coding: utf-8
from django import forms
from core.forms import BaseForm
from django.core.validators import RegexValidator


class InBoundForm(forms.Form):
    multi_id_check = RegexValidator("^(\d+,)*\d+$", u"只能填写多个订货单id，中间用英文,隔开")
    inbound_id = forms.IntegerField(required=False, initial=0)
    supplier_id = forms.IntegerField(required=False, initial=0)
    orderlist_id = forms.CharField(required=False, validators=[multi_id_check], initial='')
    express_no = forms.CharField(required=False, initial='')


class MatchOrderListsForm(BaseForm):
    inbound_skus = forms.CharField(required=False, initial='{}')


class CreateInBoundForm(BaseForm):
    inbound_skus = forms.CharField(required=False, initial='{}')
    express_no = forms.CharField(required=False, initial='')
    orderlist_id = forms.CharField(required=False, initial=0)
    # supplier_id = forms.IntegerField()
    inbound_id = forms.IntegerField(required=False, initial=0)
    memo = forms.CharField(required=False, initial='')


class SaveInBoundForm(BaseForm):
    inbound_skus = forms.CharField(required=False, initial='{}')
    inbound_id = forms.IntegerField()
    express_no = forms.CharField(required=False, initial='')
    orderlist_id = forms.CharField(required=False, initial=0)


class SaveMemoForm(BaseForm):
    inbound_id = forms.IntegerField()
    memo = forms.CharField(required=False)
    inbound_skus = forms.CharField(required=False)


class SaveDistrictsForm(BaseForm):
    inbound_id = forms.IntegerField()
    inbound_skus = forms.CharField(required=False)


class DealForm(BaseForm):
    rg_id = forms.IntegerField()
    receive_method = forms.IntegerField()
    amount = forms.FloatField()
    note = forms.CharField(required=False)
    attachment = forms.CharField(required=False)
    transaction_no = forms.CharField(required=False)

