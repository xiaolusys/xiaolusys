# coding=utf-8
from django.contrib import admin
from core.utils.modelutils import get_class_fields
from statistics.models import SaleOrderStatsRecord, SaleStats, ProductStockStat
from statistics import constants


class SaleStatsAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'parent_id',
        'current_id',
        'date_field',
        'name',
        'pic_display',
        'num',
        'payment',
        'uni_key',
        'record_type',
        'status'
    )
    list_per_page = 50
    readonly_fields = get_class_fields(SaleStats)
    list_filter = ('record_type', 'date_field', 'status')
    search_fields = ['id', 'parent_id', 'current_id', 'name', 'uni_key']

    class Media:
        js = ("layer-v1.9.2/layer/layer.js",
              "layer-v1.9.2/layer/extend/layer.ext.js",
              "statistics/js/level-statistics.js")

    def pic_display(self, obj):
        if obj.record_type < constants.TYPE_SUPPLIER:
            return '<a onclick="displayPic(\'{0}\')">查看图片</a>'.format(obj.pic_path)
        elif obj.record_type == constants.TYPE_SUPPLIER:
            return '<a target="_blank" href="{0}">供应商网址</a>'.format(obj.pic_path)
        else:
            return obj.pic_path

    pic_display.allow_tags = True
    pic_display.short_description = u'链接信息'


admin.site.register(SaleStats, SaleStatsAdmin)


class SaleOrderStatsRecordAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'oid',
        'sku_id',
        'name',
        'pic_display',
        'num',
        'payment',
        'pay_time',
        'date_field',
        'status',
        'return_goods'
    )
    list_per_page = 50
    list_filter = ('pay_time', 'status')
    search_fields = ['id', 'oid', 'sku_id', 'name']
    readonly_fields = get_class_fields(SaleOrderStatsRecord)

    def pic_display(self, obj):
        html = '<a onclick="displayPic(\'{0}\')">点击看图</a>'.format(obj.pic_path)
        return html

    pic_display.allow_tags = True
    pic_display.short_description = u'图片'

    class Media:
        js = ("layer-v1.9.2/layer/layer.js",
              "layer-v1.9.2/layer/extend/layer.ext.js",
              "statistics/js/level-statistics.js")


admin.site.register(SaleOrderStatsRecord, SaleOrderStatsRecordAdmin)


class ProductStockStatAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'parent_id',
        'current_id',
        'date_field',
        'name',
        'pic_path',
        'quantity',
        'sku_inferior_num',
        'amount',
        'uni_key',
        'record_type'
    )
    list_per_page = 50


admin.site.register(ProductStockStat, ProductStockStatAdmin)
