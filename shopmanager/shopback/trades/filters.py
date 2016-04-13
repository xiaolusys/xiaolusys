# coding: utf-8
import datetime

from django.db import models
from shopback.trades.models import MergeTrade, SYS_TRADE_STATUS
from shopback import paramconfig as pcfg

from core.filters import SimpleListFilter


class TradeStatusFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    title = u'系统状态'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'sys_status'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return SYS_TRADE_STATUS

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        status_name = self.value()
        if not status_name:
            return queryset
        elif status_name == pcfg.WAIT_AUDIT_STATUS:
            return queryset.filter(sys_status__in=(pcfg.WAIT_AUDIT_STATUS,
                                                   pcfg.WAIT_CHECK_BARCODE_STATUS,
                                                   pcfg.WAIT_SCAN_WEIGHT_STATUS),
                                   can_review=False) \
                .exclude(reason_code='',
                         is_express_print=True,
                         sys_status__in=(pcfg.WAIT_CHECK_BARCODE_STATUS,
                                         pcfg.WAIT_SCAN_WEIGHT_STATUS))

        else:
            return queryset.filter(sys_status=status_name)


class OrderPendingStatusFilter(SimpleListFilter):
    title = u'待处理状态'
    parameter_name = 'order_pending_status'

    def lookups(self, request, model_admin):
        return (('1', u'全部'), ('2', u'待处理'))

    def queryset(self, request, queryset):
        v = self.value()
        if v and v == '2':
            return queryset.filter(
                merge_trade__type__in=[pcfg.SALE_TYPE, pcfg.DIRECT_TYPE,
                                       pcfg.REISSUE_TYPE, pcfg.EXCHANGE_TYPE],
                merge_trade__sys_status__in=
                [pcfg.WAIT_AUDIT_STATUS, pcfg.WAIT_PREPARE_SEND_STATUS,
                 pcfg.WAIT_CHECK_BARCODE_STATUS, pcfg.WAIT_SCAN_WEIGHT_STATUS,
                 pcfg.REGULAR_REMAIN_STATUS],
                sys_status=pcfg.IN_EFFECT)
        return queryset
