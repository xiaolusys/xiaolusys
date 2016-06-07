# coding: utf-8

from django import forms

from core.forms import BaseForm

class ConfirmBillForm(BaseForm):
    bill_id = forms.IntegerField()
    transaction_no = forms.CharField()
    amount = forms.FloatField()
