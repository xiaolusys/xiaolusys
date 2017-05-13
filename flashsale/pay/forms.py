# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from django import forms

from .models import Envelop, CustomShare, Productdetail, ModelProduct

class ModelProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ModelProductForm, self).__init__(*args, **kwargs)

    class Meta:
        model = ModelProduct
        exclude = ()

    def clean(self):
        cleaned_data = super(ModelProductForm, self).clean()
        shelf_status  = cleaned_data.get('shelf_status')
        offshelf_time = cleaned_data.get('offshelf_time')
        onshelf_time  = cleaned_data.get('onshelf_time')

        if shelf_status == ModelProduct.ON_SHELF and not (onshelf_time and offshelf_time):
            raise forms.ValidationError('请输入上下架时间')

        if shelf_status == ModelProduct.ON_SHELF and onshelf_time >= offshelf_time:
            raise forms.ValidationError('上架时间必须在下架时间之前')



class EnvelopForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EnvelopForm, self).__init__(*args, **kwargs)
        self.initial['amount'] = self.instance.get_amount_display()

    amount = forms.FloatField(label=u'红包金额', min_value=0)

    class Meta:
        model = Envelop
        exclude = ()

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        return int(amount * 100)


class CustomShareForm(forms.ModelForm):
    desc = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = CustomShare
        exclude = ()

try:
    from flashsale.xiaolumm.models.models_rebeta import AgencyOrderRebetaScheme
except ImportError:
    func_rebeta_scheme_list = lambda: ('0', '未设置返利计划')
else:
    def func_rebeta_scheme_list():
        schemes = AgencyOrderRebetaScheme.objects.filter(status=AgencyOrderRebetaScheme.NORMAL)
        scheme_tuple = list(schemes.values_list('id', 'name'))
        scheme_tuple.insert(0, ('0', '未设置返利计划'))
        return scheme_tuple


class ProductdetailForm(forms.ModelForm):
    rebeta_scheme_id = forms.ChoiceField(label='返利计划')

    #     ware_by = forms.ModelChoiceField(queryset=func_ware_list())
    def __init__(self, *args, **kwargs):
        super(ProductdetailForm, self).__init__(*args, **kwargs)
        # access object through self.instance...
        self.fields['rebeta_scheme_id'].choices = func_rebeta_scheme_list()

    class Meta:
        model = Productdetail
        exclude = ()
