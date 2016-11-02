# -*- coding:utf8 -*-
from django import forms
from .models import ComposeRule

try:
    from shopback.users.models import User
except ImportError:
    func_user_list = lambda: ((ComposeRule.DEFAULT_SELLER_CODE, u'==全部店铺=='),)
else:
    def func_ware_list():
        users = User.objects.filter(status=User.NORMAL)
        user_list = [(ComposeRule.DEFAULT_SELLER_CODE, u'==全部店铺==')]
        user_tuple = users.values_list('id', 'nick')
        user_list.extend(user_tuple)
        return user_list


class UserForm(forms.ModelForm):
    seller_id = forms.ChoiceField(label='所属店铺')

    #     ware_by = forms.ModelChoiceField(queryset=func_ware_list())
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        # access object through self.instance...
        self.fields['seller_id'].choices = func_ware_list()

    class Meta:
        model = User
        exclude = ()
