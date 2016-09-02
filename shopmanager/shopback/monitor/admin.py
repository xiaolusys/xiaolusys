from django.contrib import admin
from shopback.monitor.models import DayMonitorStatus, TradeExtraInfo, SystemConfig, Reason, XiaoluSwitch


class SystemConfigAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'is_rule_auto', 'is_sms_auto', 'is_flag_auto', 'client_num', 'per_request_num', 'normal_print_limit'
    , 'jhs_logistic_code', 'category_updated', 'mall_order_updated', 'fenxiao_order_updated')
    list_display_links = ('id',)


admin.site.register(SystemConfig, SystemConfigAdmin)


class DayMonitorStatusAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'year', 'month', 'day', 'update_trade_increment', 'update_purchase_increment')
    list_display_links = ('user_id',)
    list_filter = ('update_trade_increment', 'update_purchase_increment')
    search_fields = ['user_id', 'year', 'month', 'day']


admin.site.register(DayMonitorStatus, DayMonitorStatusAdmin)


class TradeExtraInfoAdmin(admin.ModelAdmin):
    list_display = ('tid', 'is_update_amount', 'is_update_logistic', 'modified')
    list_display_links = ('tid',)
    # list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'modified'

    list_filter = ('is_update_amount', 'is_update_logistic')
    search_fields = ['tid', ]


admin.site.register(TradeExtraInfo, TradeExtraInfoAdmin)


class ReasonAdmin(admin.ModelAdmin):
    list_display = ('id', 'reason_text', 'priority', 'created')
    list_display_links = ('id',)
    # list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'

    # list_filter = ('is_update_amount','is_update_logistic')
    search_fields = ['id', 'reason_text']


admin.site.register(Reason, ReasonAdmin)


class XiaoluSwitchAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'start_time', 'end_time', 'description', 'responsible', 'status', 'modified', 'created')
    search_fields = ('title', 'description', 'responsible')
    list_filter = ('status', )

admin.site.register(XiaoluSwitch, XiaoluSwitchAdmin)

