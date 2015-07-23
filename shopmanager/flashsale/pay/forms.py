#-*- coding:utf-8 -*-
from django import forms
from .models import Envelop

class EnvelopForm( forms.ModelForm ):
    
    def __init__(self, *args, **kwargs):
        super(EnvelopForm, self).__init__(*args, **kwargs)
        self.initial['amount']    = self.instance.get_amount_display()
    
    amount    = forms.FloatField(label=u'红包金额',min_value=0)
    
    class Meta:
        model = Envelop
    
    def  clean_amount(self):
        amount = self.cleaned_data['amount']
        return int(amount * 100)
    
