from django import forms


class ExchangeTradeForm(forms.Form):

    trade_id  = forms.BigIntegerField(required=True)
    sellerId = forms.BigIntegerField(required=True)

    buyer_nick         = forms.CharField(max_length=64,required=True)
    receiver_name      = forms.CharField(max_length=64,required=True)
    receiver_state     = forms.CharField(max_length=16,required=True)
    receiver_city      = forms.CharField(max_length=16,required=True)
    receiver_district   = forms.CharField(max_length=16,required=False)
    receiver_address    = forms.CharField(max_length=128,required=True)
    
    receiver_mobile   = forms.CharField(max_length=20,required=False)
    receiver_phone    = forms.CharField(max_length=20,required=False)
  