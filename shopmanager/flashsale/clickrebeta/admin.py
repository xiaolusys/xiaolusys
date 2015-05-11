#-*- coding:utf8 -*-
from django.contrib import admin


from .models import StatisticsShopping, StatisticsShoppingByDay
from django import forms


class StatisticsShoppingForm( forms.ModelForm ):

    def __init__(self, *args, **kwargs):
        super(StatisticsShoppingForm, self).__init__(*args, **kwargs)
        self.initial['wxorderamount']    = self.instance.order_cash()
        self.initial['tichengcount'] = self.instance.ticheng_cash()

    wxorderamount= forms.FloatField(label=u'订单价格',min_value=0)
    tichengcount = forms.FloatField(label=u'提成',min_value=0)

    class Meta:
        model = StatisticsShopping

    def  clean_wxorderamount(self):
        wxorderamount = self.cleaned_data['wxorderamount']
        return int(wxorderamount * 100)

    def  clean_tichengcount(self):
        tichengcount = self.cleaned_data['tichengcount']
        return int(tichengcount * 1000)

class StatisticsShoppingAdmin(admin.ModelAdmin):
    form = StatisticsShoppingForm
    list_display = ('linkid', 'linkname', 'openid','wxorderid','order_cash','ticheng_cash','shoptime')
    list_filter = ('linkid',)
    search_fields = ['linkid', 'openid']


admin.site.register(StatisticsShopping, StatisticsShoppingAdmin)
admin.site.register(StatisticsShoppingByDay)