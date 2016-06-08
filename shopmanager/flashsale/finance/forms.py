# coding: utf-8

from django import forms

from core.forms import BaseForm

class ConfirmBillForm(BaseForm):
    bill_id = forms.IntegerField()
    transaction_no = forms.CharField()
    amount = forms.FloatField()

class DealForm(BaseForm):
    bill_id = forms.IntegerField()
    receive_method = forms.IntegerField()
    amount = forms.FloatField()
    note = forms.CharField()
    attachment = forms.CharField()
    transaction_no = forms.CharField(required=False)
