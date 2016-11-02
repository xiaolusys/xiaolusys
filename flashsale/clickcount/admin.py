# coding:utf-8
import re
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList

from core.admin import ApproxAdmin
from core.filters import DateFieldListFilter
from shopapp.weixin.models import WXOrder
from .models import Clicks, UserClicks, ClickCount, WeekCount


class ClicksChangeList(ChangeList):
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
            if re.compile('[\d]{11}').match(search_q):
                openids = WXOrder.objects.filter(receiver_mobile=search_q).values('buyer_openid').distinct()
                openids = [o['buyer_openid'] for o in openids]
                qs = qs.filter(openid__in=openids)
                return qs
            if re.compile('[\d]{1,10}').match(search_q):
                return qs.filter(linkid=search_q)
            qs = qs.filter(openid=search_q)
            return qs

        super_ = super(ClicksChangeList, self)
        return super_.get_queryset(request)


class ClicksAdmin(ApproxAdmin):
    list_display = ('linkid', 'openid', 'isvalid', 'click_time')
    list_filter = ('isvalid', ('click_time', DateFieldListFilter),)
    search_fields = ['=linkid', '=openid']

    list_per_page = 50

    def get_changelist(self, request, **kwargs):
        return ClicksChangeList


admin.site.register(Clicks, ClicksAdmin)


class UserClicksAdmin(ApproxAdmin):
    list_display = ('unionid', 'visit_days', 'click_start_time', 'click_end_time')
    list_filter = (('click_start_time', DateFieldListFilter), ('click_end_time', DateFieldListFilter),)
    search_fields = ['=unionid', ]


admin.site.register(UserClicks, UserClicksAdmin)


class ClickCountAdmin(ApproxAdmin):
    list_display = ('linkid', 'weikefu', 'mobile', 'user_num', 'valid_num',
                    'click_num', 'date', 'write_time', 'username')

    list_display_links = ['linkid', 'username']
    list_filter = ('date', 'username')

    search_fields = ['=linkid', '=mobile']


admin.site.register(ClickCount, ClickCountAdmin)


class WeekCountAdmin(ApproxAdmin):
    list_display = ('linkid', 'weikefu', 'buyercount', 'user_num', 'valid_num', 'ordernumcount',
                    'conversion_rate', 'week_code', 'write_time')

    list_display_links = ['linkid', 'week_code']
    list_filter = ('week_code',)

    search_fields = ['=linkid', '=week_code']


admin.site.register(WeekCount, WeekCountAdmin)
