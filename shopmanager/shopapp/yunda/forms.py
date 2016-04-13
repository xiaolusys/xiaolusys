# -*- coding:utf8 -*-
from django import forms
from .models import YundaCustomer

try:
    from shopback.warehouse.models import WareHouse
except ImportError:
    func_ware_list = lambda: ()
else:
    def func_ware_list():
        wares = WareHouse.objects.filter(in_active=True)
        ware_tuple = wares.values_list('id', 'ware_name')
        return ware_tuple


class YundaCustomerForm(forms.ModelForm):
    ware_by = forms.ChoiceField(label='所属仓库')

    #     ware_by = forms.ModelChoiceField(queryset=func_ware_list())
    def __init__(self, *args, **kwargs):
        super(YundaCustomerForm, self).__init__(*args, **kwargs)
        # access object through self.instance...
        self.fields['ware_by'].choices = func_ware_list()

    class Meta:
        model = YundaCustomer
        exclude = ()

# widgets = {
#             'ware_by' : forms.Select(choices=((1,'abc'),))
#         }
