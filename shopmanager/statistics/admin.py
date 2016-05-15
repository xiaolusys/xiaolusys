from django.contrib import admin
from statistics.models import StatisticSaleNum


class StatisticSaleNumAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'upper_grade',
        'target_id',
        'pay_date',
        'uniq_id',
        'record_type',
        'sale_num',
        'sale_value',
        'stock_out_num',
        'before_post_ref_num',
        'after_post_ref_num',
    )

    list_filter = ('record_type', 'pay_date')


admin.site.register(StatisticSaleNum, StatisticSaleNumAdmin)
