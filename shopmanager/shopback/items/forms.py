#-*- coding:utf8 -*-
from django import forms
from .models import Product

class ProductModelForm( forms.ModelForm ):
    
    pic_path = forms.CharField(label=u'图片链接',widget=forms.TextInput(attrs={'size':'60','maxlength':'256'}))
    
    class Meta:
        model = Product