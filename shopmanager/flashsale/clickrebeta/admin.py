# -*- coding:utf8 -*-
from django.contrib import admin
from shopback.base.options import DateFieldListFilter
from .models import StatisticsShopping, StatisticsShoppingByDay
from django import forms


class StatisticsShoppingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(StatisticsShoppingForm, self).__init__(*args, **kwargs)
        self.initial['wxorderamount'] = self.instance.order_cash()
        self.initial['tichengcount'] = self.instance.ticheng_cash()

    wxorderamount = forms.FloatField(label=u'订单价格', min_value=0)
    tichengcount = forms.FloatField(label=u'提成', min_value=0)

    class Meta:
        model = StatisticsShopping

    def clean_wxorderamount(self):
        wxorderamount = self.cleaned_data['wxorderamount']
        return int(wxorderamount * 100)

    def clean_tichengcount(self):
        tichengcount = self.cleaned_data['tichengcount']
        return int(tichengcount * 1000)


class StatisticsShoppingAdmin(admin.ModelAdmin):
    form = StatisticsShoppingForm
    list_display = ('linkid', 'linkname', 'openid', 'wxorderid', 'order_cash', 'ticheng_cash', 'shoptime')
    list_filter = (('shoptime',DateFieldListFilter),)
    search_fields = ['linkid', 'openid']


admin.site.register(StatisticsShopping, StatisticsShoppingAdmin)


class StatisticsShoppingByDayAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(StatisticsShoppingByDayAdminForm, self).__init__(*args, **kwargs)
        self.initial['orderamountcount'] = self.instance.order_cash()
        self.initial['todayamountcount'] = self.instance.today_cash()

    orderamountcount = forms.FloatField(label=u'订单总价', min_value=0)
    todayamountcount = forms.FloatField(label=u'提成总价', min_value=0)

    class Meta:
        model = StatisticsShopping

    def clean_orderamountcount(self):
        orderamountcount = self.cleaned_data['orderamountcount']
        return int(orderamountcount * 100)

    def clean_todayamountcount(self):
        todayamountcount = self.cleaned_data['todayamountcount']
        return int(todayamountcount * 1000)

class StatisticsShoppingByDayAdmin(admin.ModelAdmin):
    form = StatisticsShoppingByDayAdminForm
    list_display = ('linkid', 'linkname', 'ordernumcount', 'order_cash', 'today_cash', 'tongjidate')
    list_filter = ('linkid',)
    search_fields = ['linkid', 'tongjidate']


admin.site.register(StatisticsShoppingByDay, StatisticsShoppingByDayAdmin)