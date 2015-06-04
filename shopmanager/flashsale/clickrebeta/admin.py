# -*- coding:utf8 -*-
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django import forms

from shopback.base.options import DateFieldListFilter
from .models import StatisticsShopping, StatisticsShoppingByDay



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
        return int(tichengcount * 100)

import re
from django.db.models import Q
from shopapp.weixin.models import WXOrder

class StatisticsShoppingChangeList(ChangeList):
    
    def get_query_set(self,request):
        
        search_q = request.GET.get('q','').strip()
        if search_q :
            (self.filter_specs, self.has_filters, remaining_lookup_params,
             use_distinct) = self.get_filters(request)
            
            qs = self.root_query_set
            for filter_spec in self.filter_specs:
                new_qs = filter_spec.queryset(request, qs)
                if new_qs is not None:
                    qs = new_qs
            
            if re.compile('^[\d]{11}$').match(search_q):
                openids = WXOrder.objects.filter(receiver_mobile=search_q).values('buyer_openid').distinct()
                openids = [o['buyer_openid'] for o in openids]
           
                qs = qs.filter(openid__in=openids)
                return qs
    
            qs = qs.filter(Q(openid=search_q)|Q(wxorderid=search_q))
            return qs
        
        return super(StatisticsShoppingChangeList,self).get_query_set(request)


class StatisticsShoppingAdmin(admin.ModelAdmin):
    form = StatisticsShoppingForm
    list_display = ('linkid', 'linkname', 'openid','wxordernick', 'wxorderid', 'order_cash', 'ticheng_cash', 'shoptime','status')
    list_filter = ('status',('shoptime',DateFieldListFilter),)
    search_fields = ['openid','wxorderid']
    
    def get_changelist(self, request, **kwargs):

        return StatisticsShoppingChangeList

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
        return int(todayamountcount * 100)
    

class StatisticsShoppingByDayAdmin(admin.ModelAdmin):
    form = StatisticsShoppingByDayAdminForm
    list_display = ('linkid', 'linkname','buyercount', 'ordernumcount', 'order_cash', 'today_cash', 'tongjidate')
    list_filter = (('tongjidate',DateFieldListFilter),)
    search_fields = ['linkid']


admin.site.register(StatisticsShoppingByDay, StatisticsShoppingByDayAdmin)

