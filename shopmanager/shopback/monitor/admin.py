from django.contrib import admin
from shopback.monitor.models import DayMonitorStatus,TradeExtraInfo



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
    list_display = ('tid','is_update_amount','is_update_logistic','is_picking_print','is_send_sms','modified','seller_memo')
    list_display_links = ('tid',)
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'modified'

    list_filter = ('is_update_amount','is_update_logistic','is_picking_print','is_send_sms')
    search_fields = ['tid',]


admin.site.register(TradeExtraInfo, TradeExtraInfoAdmin)