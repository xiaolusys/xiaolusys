#-*- coding:utf8 -*-
from django import forms

from .models import Clicks,XiaoluMama,AgencyLevel,CashOut,CarryLog

class XiaoluMamaForm( forms.ModelForm ):
    
    def __init__(self, *args, **kwargs):
        super(XiaoluMamaForm, self).__init__(*args, **kwargs)
        self.initial['cash']    = self.instance.get_cash_display()
        self.initial['pending'] = self.instance.get_pending_display()
    
    cash    = forms.FloatField(label=u'可用现金',min_value=0)
    pending = forms.FloatField(label=u'冻结现金',min_value=0)
    
    class Meta:
        model = XiaoluMama
    
    def  clean_cash(self):
        cash = self.cleaned_data['cash']
        return int(cash * 100)
    
    def  clean_pending(self):
        pending = self.cleaned_data['pending']
        return int(pending * 100)

    
class CashOutForm( forms.ModelForm ):
    
    def __init__(self, *args, **kwargs):
        super(CashOutForm, self).__init__(*args, **kwargs)
        self.initial['value']    = self.instance.get_value_display()
    
    value    = forms.FloatField(label=u'现金',min_value=0)
    
    class Meta:
        model = CashOut
    
    def  clean_value(self):
        value = self.cleaned_data['value']
        return int(value * 100) 
    

class CarryLogForm( forms.ModelForm ):
    
    def __init__(self, *args, **kwargs):
        super(CarryLogForm, self).__init__(*args, **kwargs)
        self.initial['value']    = self.instance.get_value_display()
    
    value    = forms.FloatField(label=u'现金',min_value=0)
    
    class Meta:
        model = CashOut
    
    def  clean_value(self):
        value = self.cleaned_data['value']
        return int(value * 100)     

