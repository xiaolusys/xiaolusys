# -*- coding:utf-8 -*-
from django.contrib import admin
from flashsale.kefu.models import KefuPerformance


class KefuPerformanceAdmin(admin.ModelAdmin):
    list_display = (
        'kefu_name', 'operation', 'trade_id', 'operate_time')
    list_filter = ('created', 'kefu_name')
    search_fields = ['kefu_name', 'trade_id']
    date_hierarchy = 'created'

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ('kefu_id', 'kefu_name', 'operation', 'trade_id', 'operate_time')
        return self.readonly_fields


admin.site.register(KefuPerformance, KefuPerformanceAdmin)
