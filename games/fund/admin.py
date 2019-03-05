# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.contrib import admin

from .models import FundBuyerAccount, FundNotifyMsg

@admin.register(FundBuyerAccount)
class FundBuyerAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'buyer_name', 'mobile', 'buy_amount', 'settled_earned_profit', 'annual_yield_rate',
                    'total_buy_amount', 'total_earned_profit', 'total_cashout', 'last_buy_date', 'created')
    list_filter = ('status','last_buy_date', 'created')
    search_fields = ['=id', '=buyer_name', '=mobile']
    list_per_page = 100


@admin.register(FundNotifyMsg)
class FundNotifyMsgAdmin(admin.ModelAdmin):
    list_display = ('id', 'fund_buyer', 'send_type', 'is_send','send_time', 'created')
    list_filter = ('is_send', 'send_time', 'created')
    search_fields = ['=id', '=fund_buyer__mobile']
    list_per_page = 100


