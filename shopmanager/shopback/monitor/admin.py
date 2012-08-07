from django.contrib import admin
from shopback.monitor.models import DayMonitorStatus,TradeExtraInfo,SystemConfig


class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ('id','is_rule_auto','is_sms_auto','is_confirm_delivery_auto')
    list_display_links = ('id',)

admin.site.register(SystemConfig,SystemConfigAdmin)


class DayMonitorStatusAdmin(admin.ModelAdmin):
    list_display = ('user_id','year','month','day','update_trade_increment','update_purchase_increment')
    list_display_links = ('user_id',)
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'modified'
    #ordering = ['created_at']

    list_filter = ('update_trade_increment','update_purchase_increment')
    search_fields = ['user_id','year','month','day']


admin.site.register(DayMonitorStatus, DayMonitorStatusAdmin)


class TradeExtraInfoAdmin(admin.ModelAdmin):
    list_display = ('tid','is_update_amount','is_update_logistic','modified')
    list_display_links = ('tid',)
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'modified'

    list_filter = ('is_update_amount','is_update_logistic')
    search_fields = ['tid',]


admin.site.register(TradeExtraInfo, TradeExtraInfoAdmin)