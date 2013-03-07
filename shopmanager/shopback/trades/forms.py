import sys
from django import forms


class ExchangeTradeForm(forms.Form):

    trade_id  = forms.IntegerField(min_value=0,max_value=sys.float_info.max,required=True)
    sellerId = forms.IntegerField(min_value=0,max_value=sys.float_info.max,required=True)

    buyer_nick         = forms.CharField(max_length=64,required=True)
    receiver_name      = forms.CharField(max_length=64,required=True)
    receiver_state     = forms.CharField(max_length=16,required=True)
    receiver_city      = forms.CharField(max_length=16,required=True)
    receiver_district   = forms.CharField(max_length=16,required=False)
    receiver_address    = forms.CharField(max_length=128,required=True)
    
    receiver_mobile   = forms.CharField(max_length=20,required=False)
    receiver_phone    = forms.CharField(max_length=20,required=False)
    
    
class StatisticMergeOrderForm(forms.Form):
    
    df   = forms.DateField(input_formats='%Y-%m-%d %H:%M:%S',required=False)
    dt   = forms.DateField(input_formats='%Y-%m-%d %H:%M:%S',required=False)
    outer_id      = forms.CharField(max_length=64,required=False)
    statistic_by  = forms.CharField(max_length=64,required=False)
    
    