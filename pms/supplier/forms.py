# coding: utf-8

import datetime

from django import forms
from django.core.validators import RegexValidator

from core.forms import BaseForm
from .models import SaleSupplier, SupplierZone


def func_supplier_zone_list():
    supplier_zone = SupplierZone.objects.all()
    supplier_zone_tuple = supplier_zone.values_list('id', 'name')
    return supplier_zone_tuple


class SaleSupplierForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SaleSupplierForm, self).__init__(*args, **kwargs)
        self.fields['supplier_zone'].choices = func_supplier_zone_list()

        supplier_zone = forms.ChoiceField(label=u'供应商区域', required=True)

    supplier_name = forms.CharField(label=u'供应商', required=True)
    contact = forms.CharField(label=u'联系人',
                              required=True,
                              validators=[RegexValidator(ur"^[\u4e00-\u9fa5]+$", message=u"请输入汉字")])
    mobile = forms.CharField(label=u'手机号',
                             required=True,
                             validators=[RegexValidator('^1[34578][0-9]{9}$', message=u"请输入正确的手机号码")])
    address = forms.CharField(label=u'地址',
                              required=True,
                              widget=forms.TextInput(attrs={'size': '60', 'maxlength': '256'}),
                              validators=[RegexValidator(ur"^[\u4e00-\u9fa5]+[\u4e00-\u9fa50-9_#\-\(\)\w\s\/]+$",
                                                         message=u"请输入汉字及数字")])

    class Meta:
        model = SaleSupplier
        exclude = ()


class ScheduleBatchSetForm(BaseForm):
    is_watermark = forms.BooleanField(required=False)
    cancel_watermark = forms.BooleanField(required=False)
    is_seckill = forms.BooleanField(required=False)
    cancel_seckill = forms.BooleanField(required=False)
    is_recommend = forms.BooleanField(required=False)
    cancel_recommend = forms.BooleanField(required=False)
    rebeta_schema_id = forms.IntegerField(required=False)
    price = forms.FloatField(required=False)
    order_weight = forms.IntegerField(required=False)
    sync_stock = forms.BooleanField(required=False)
    #sale_product_ids = forms.CharField(required=False, initial='[]')
    detail_ids = forms.CharField(required=False, initial='[]')
    onshelf_date = forms.DateField(required=False)


class SaleProductManageExportForm(BaseForm):
    from_date = forms.DateField()
    end_date = forms.DateField(initial=datetime.date.today(), required=False)
