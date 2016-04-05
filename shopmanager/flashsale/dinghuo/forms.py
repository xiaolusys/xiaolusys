# coding: utf-8

from django import forms

from core.forms import BaseForm


class InBoundListForm(BaseForm):
    supplier = forms.CharField(required=False)
    express_no = forms.CharField(required=False)
    target_id = forms.IntegerField(required=False, initial=0)
    sent_from = forms.IntegerField(required=False, initial=1)
    inbound_id = forms.IntegerField(required=False, initial=0)

    @property
    def json(self):
        ca = self.cleaned_attrs
        return {
            'supplier': ca.supplier,
            'express_no': ca.express_no,
            'target_id': ca.target_id,
            'sent_from': ca.sent_from,
            'inbound_id': ca.inbound_id
        }


class EditInBoundForm(InBoundListForm):
    inbound_id = forms.IntegerField(required=False, initial=0)
    skus = forms.CharField(required=False, initial='[]')
