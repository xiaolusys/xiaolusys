# -*- coding:utf-8 -*-
from django import forms

from .models import Envelop, CustomShare, Productdetail


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
