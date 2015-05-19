# -*- coding:utf8 -*-
from django.contrib import admin
from shopback.base.options import DateFieldListFilter
from .models import DailyStat
from django import forms


class DailyStatForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DailyStatForm, self).__init__(*args, **kwargs)
        self.initial['total_payment'] = self.instance.total_payment_cash()

    total_payment = forms.FloatField(label=u'日成交额', min_value=0)

    class Meta:
        model = DailyStat

    def clean_total_payment(self):
        total_payment = self.cleaned_data['total_payment']
        return int(total_payment * 100)



class DailyStatAdmin(admin.ModelAdmin):
    form = DailyStatForm
    list_display = ('day_date', 'total_click_count', 'total_valid_count','total_visiter_num', 
                    'total_payment', 'total_order_num', 'total_buyer_num', 'total_old_buyer_num',
                    'get_pice_per_customer_display', 'get_daily_roi_display')
    list_filter = (('day_date',DateFieldListFilter),)
    search_fields = ['day_date']


admin.site.register(DailyStat, DailyStatAdmin)