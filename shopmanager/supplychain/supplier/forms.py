#-*- coding:utf8 -*-
from django.core.validators import RegexValidator
from django import forms
from .models import SaleSupplier

class SaleSupplierForm(forms.ModelForm):
    
    supplier_name = forms.CharField(label=u'供应商',required=True)
    contact  = forms.CharField(label=u'联系人',required=True,validators=[RegexValidator(ur"^[\u4e00-\u9fa5]+$", message=u"请输入汉字")])
    mobile   = forms.CharField(label=u'手机号',required=True,validators=[RegexValidator('^1[34578][0-9]{9}$', message=u"请输入正确的手机号码")])
    address  = forms.CharField(label=u'地址',required=True,validators=[RegexValidator(ur"^[\u4e00-\u9fa5]+[\u4e00-\u9fa50-9]+$", message=u"请输入汉字及数字")])
    class Meta:
        model = SaleSupplier