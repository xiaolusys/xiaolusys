# coding: utf-8
from django import forms
from core.forms import BaseForm
from forms_inbound import InBoundForm, MatchOrderListsForm, CreateInBoundForm, SaveInBoundForm, SaveMemoForm, \
    SaveDistrictsForm, DealForm


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
    details = forms.CharField(required=False, initial='[]')
    images = forms.CharField(required=False, initial='[]')
    memo = forms.CharField(required=False, initial='')


class AdvanceDingHuoForm(BaseForm):
    start_date = forms.DateField(required=True)
    end_date = forms.DateField(required=True)


class InBoundForm(BaseForm):
    inbound_id = forms.IntegerField(required=False, initial=0)
    supplier_id = forms.IntegerField(required=False, initial=0)
    orderlist_id = forms.CharField(required=True, initial='')
    express_no = forms.CharField(required=True, initial='')


class MatchOrderListsForm(BaseForm):
    inbound_skus = forms.CharField(required=False, initial='{}')


class CreateInBoundForm(BaseForm):
    inbound_skus = forms.CharField(required=False, initial='{}')
    express_no = forms.CharField(required=False, initial='')
    orderlist_id = forms.CharField(required=False, initial='')
    supplier_id = forms.IntegerField(required=False)
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


class ReturnGoodsAddSkuForm(BaseForm):
    rg_id = forms.IntegerField()
    sku_id = forms.IntegerField()
    num = forms.IntegerField()
    inferior = forms.IntegerField()
