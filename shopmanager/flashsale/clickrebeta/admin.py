# -*- coding:utf8 -*-
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django import forms

from core.admin import ApproxAdmin
from core.filters import DateFieldListFilter
from .models import StatisticsShopping, OrderDetailRebeta, StatisticsShoppingByDay


class OrderDetailRebetaInline(admin.TabularInline):
    model = OrderDetailRebeta
    fields = ('detail_id', 'scheme_id', 'order_amount', 'rebeta_amount', 'pay_time', 'status')

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ('detail_id', 'rebeta_amount')
        return self.readonly_fields


class StatisticsShoppingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(StatisticsShoppingForm, self).__init__(*args, **kwargs)
        self.initial['wxorderamount'] = self.instance.order_cash()
        self.initial['rebetamount'] = self.instance.rebeta_cash()
        self.initial['tichengcount'] = self.instance.ticheng_cash()

    wxorderamount = forms.FloatField(label=u'订单价格', min_value=0)
    rebetamount = forms.FloatField(label=u'有效金额', min_value=0)
    tichengcount = forms.FloatField(label=u'提成', min_value=0)

    class Meta:
        model = StatisticsShopping
        exclude = ()

    def clean_wxorderamount(self):
        wxorderamount = self.cleaned_data['wxorderamount']
        return int(wxorderamount * 100)

    def clean_rebetamount(self):
        rebetamount = self.cleaned_data['rebetamount']
        return int(rebetamount * 100)

    def clean_tichengcount(self):
        tichengcount = self.cleaned_data['tichengcount']
        return int(tichengcount * 100)


import re
from django.db.models import Q
from shopback.trades.models import MergeTrade


class StatisticsShoppingChangeList(ChangeList):
    def get_queryset(self, request):

        search_q = request.GET.get('q', '').strip()
        if search_q:
            (self.filter_specs, self.has_filters, remaining_lookup_params,
             use_distinct) = self.get_filters(request)

            qs = self.root_queryset
            for filter_spec in self.filter_specs:
                new_qs = filter_spec.queryset(request, qs)
                if new_qs is not None:
                    qs = new_qs

            if re.compile('^[\d]{11}$').match(search_q):
                trade_ids = MergeTrade.objects.filter(receiver_mobile=search_q).values('tid').distinct()
                tids = set([o['tid'] for o in trade_ids])

                qs = qs.filter(wxorderid__in=tids)
                return qs

            if re.compile('^[\d]{1,10}$').match(search_q):
                qs = qs.filter(Q(linkid=search_q) | Q(wxorderid=search_q))
            else:
                qs = qs.filter(Q(openid=search_q) | Q(wxorderid=search_q))
            return qs

        super_ = super(StatisticsShoppingChangeList, self)
        return super_.get_queryset(request)


class StatisticsShoppingAdmin(ApproxAdmin):
    form = StatisticsShoppingForm
    list_display = (
    'linkid', 'linkname', 'openid', 'wxordernick', 'wxorderid', 'order_cash', 'ticheng_cash', 'shoptime', 'status')

    list_filter = ('status', ('shoptime', DateFieldListFilter),)

    search_fields = ['=linkid', '=openid', '=wxorderid']

    inlines = [OrderDetailRebetaInline]

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
        exclude = ()

    def clean_orderamountcount(self):
        orderamountcount = self.cleaned_data['orderamountcount']
        return int(orderamountcount * 100)

    def clean_todayamountcount(self):
        todayamountcount = self.cleaned_data['todayamountcount']
        return int(todayamountcount * 100)


class StatisticsShoppingByDayAdmin(ApproxAdmin):
    form = StatisticsShoppingByDayAdminForm
    list_display = ('linkid', 'linkname', 'buyercount', 'ordernumcount', 'order_cash', 'today_cash', 'tongjidate')
    list_filter = (('tongjidate', DateFieldListFilter),)
    search_fields = ['=linkid']


admin.site.register(StatisticsShoppingByDay, StatisticsShoppingByDayAdmin)
