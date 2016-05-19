from django.contrib import admin
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


admin.site.register(SaleOrderStatsRecord, SaleOrderStatsRecordAdmin)
