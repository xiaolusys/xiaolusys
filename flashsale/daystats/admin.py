# -*- coding:utf8 -*-
from django.contrib import admin
from core.filters import DateFieldListFilter
from .models import DailyStat, PopularizeCost
from django import forms

from core.admin import ApproxAdmin


class DailyStatForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DailyStatForm, self).__init__(*args, **kwargs)
        self.initial['total_payment'] = self.instance.get_total_payment_display()

    total_payment = forms.FloatField(label=u'日成交额', min_value=0)

    class Meta:
        model = DailyStat
        exclude = ()

    def clean_total_payment(self):
        total_payment = self.cleaned_data['total_payment']
        return int(total_payment * 100)


class DailyStatAdmin(ApproxAdmin):
    form = DailyStatForm
    list_display = ('day_date', 'total_click_count', 'total_valid_count', 'total_visiter_num', 'total_new_visiter_num',
                    'get_total_payment_display', 'total_paycash_display', 'total_coupon_display', 'total_budget_display',
                    'total_boutique_display', 'total_deposite_display', 'total_order_num',
                    'total_new_order_num', 'total_buyer_num', 'get_new_customer_num_display',
                    'get_seven_new_buyer_num', 'get_daily_rpi_display', 'get_price_per_customer_display',
                    'get_daily_roi_display')
    list_filter = (('day_date', DateFieldListFilter),)
    date_hierarchy = 'day_date'
    search_fields = ['=day_date']
    ordering = ('-day_date',)

    def total_paycash_display(self, obj):
        return '%.2f'% (obj.total_paycash / 100.0)

    def total_coupon_display(self, obj):
        return '%.2f' % (obj.total_coupon / 100.0)

    def total_budget_display(self, obj):
        return '%.2f' % (obj.total_budget / 100.0)

    def total_boutique_display(self, obj):
        return '%.2f' % (obj.total_boutique / 100.0)

    def total_deposite_display(self, obj):
        return '%.2f' % (obj.total_deposite / 100.0)



admin.site.register(DailyStat, DailyStatAdmin)


class PopularizeCostAdmin(admin.ModelAdmin):
    list_display = ('date',
                    'carrylog_order', 'carrylog_click', 'carrylog_thousand',
                    'carrylog_agency', 'carrylog_recruit','carrylog_order_buy',
                    'carrylog_cash_out', 'carrylog_deposit', 'carrylog_refund_return',
                    'carrylog_red_packet',
                    'total_incarry',
                    'total_outcarry')
    list_filter = (('date', DateFieldListFilter),)
    search_fields = ['=date']
    ordering = ('-date',)


admin.site.register(PopularizeCost, PopularizeCostAdmin)
