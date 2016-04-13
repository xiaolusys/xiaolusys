from django.contrib import admin
from shopapp.report.models import MonthTradeReportStatus


class MonthTradeReportStatusAdmin(admin.ModelAdmin):
    list_display = (
    'seller_id', 'year', 'month', 'update_order', 'update_purchase', 'update_amount', 'update_purchase_amount',
    'update_logistics', 'update_refund', 'order_task_id', 'created')
    list_display_links = ('seller_id', 'year', 'month')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    # ordering = ['created_at']

    list_filter = ('seller_id', 'year', 'month')
    search_fields = ['seller_id', 'year', 'month', 'order_task_id']


admin.site.register(MonthTradeReportStatus, MonthTradeReportStatusAdmin)
