# -*- coding:utf-8 -*-
from django.contrib import admin
from flashsale.kefu.models import KefuPerformance


class KefuPerformanceAdmin(admin.ModelAdmin):
    list_display = (
        'kefu_name', 'operation', 'trade_id', 'operate_time')
    list_filter = ('created', 'kefu_name')
    search_fields = ['kefu_name', 'trade_id']
    date_hierarchy = 'created'
admin.site.register(KefuPerformance, KefuPerformanceAdmin)




