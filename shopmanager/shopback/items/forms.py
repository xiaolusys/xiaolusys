#-*- coding:utf8 -*-
import sys
from django import forms
from .models import Product

class ProductModelForm( forms.ModelForm ):
    
    pic_path = forms.CharField(label=u'图片链接',widget=forms.TextInput(attrs={'size':'60','maxlength':'256'}))
    
    class Meta:
        model = Product
        

class ProductScanForm(forms.Form):

    wave_no  = forms.CharField(max_length=32,required=True)
    barcode  = forms.CharField(max_length=32,required=True)

    num      = forms.IntegerField(min_value=1,max_value=10000,required=True)
    