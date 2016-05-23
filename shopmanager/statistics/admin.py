from django.contrib import admin
from core.utils.modelutils import get_class_fields
from statistics.models import SaleOrderStatsRecord, SaleStats


class SaleStatsAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'parent_id',
        'current_id',
        'date_field',
        'name',
        'pic_path',
        'num',
        'payment',
        'uni_key',
        'record_type',
        'status'
    )
    list_per_page = 50
    readonly_fields = get_class_fields(SaleStats)
    list_filter = ('record_type', 'date_field', 'status')


admin.site.register(SaleStats, SaleStatsAdmin)


class SaleOrderStatsRecordAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'oid',
        'outer_id',
        'sku_id',
        'name',
        'pic_path',
        'num',
        'payment',
        'pay_time',
        'date_field',
        'status',
        'return_goods'
    )
    list_per_page = 50
    list_filter = ('pay_time', 'status')
    readonly_fields = get_class_fields(SaleOrderStatsRecord)

admin.site.register(SaleOrderStatsRecord, SaleOrderStatsRecordAdmin)
