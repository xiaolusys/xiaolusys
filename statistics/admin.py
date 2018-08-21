# coding=utf-8
from django.contrib import admin
from core.utils.modelutils import get_class_fields
from statistics.models import SaleOrderStatsRecord, SaleStats, ProductStockStat, XlmmDailyStat
from statistics import constants
from statistics.models import DailyStat, ModelStats


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
        'timely_type',
        'record_type',
        'status'
    )
    list_per_page = 50
    readonly_fields = get_class_fields(SaleStats)
    list_filter = ('record_type', 'date_field', 'status', 'timely_type')
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

    # readonly_fields = get_class_fields(SaleOrderStatsRecord)

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
        'inferior_num',
        'amount',
        'uni_key',
        'record_type',
        'timely_type'
    )
    list_per_page = 50
    list_filter = ('record_type', 'date_field', 'timely_type')
    search_fields = ['id', 'parent_id', 'current_id', 'name', 'uni_key']


admin.site.register(ProductStockStat, ProductStockStatAdmin)


class DailyStatAdmin(admin.ModelAdmin):
    list_display = (
        'daytime',
        'total_stock',
        'total_amount',
        'total_youni_stock',
        'total_youni_amount',
        'total_noyouni_stock',
        'total_noyouni_amount',
        'total_order',
        'total_purchase',
        'note'
    )
    list_per_page = 50
    list_filter = ()
    search_fields = ['id', 'daytime']


admin.site.register(DailyStat, DailyStatAdmin)


class ModelStatsAdmin(admin.ModelAdmin):
    list_display = (
        "pic_display",
        "model_name_display",
        "model_sale_link",
        "schedule_manager_info",
        "category_name",
        "supplier_link",
        "pay_num",
        "no_pay_num",
        "cancel_num",
        "out_stock_num",
        "return_good_num",
        "payment",
        "agent_price",
        "cost"
    )
    list_per_page = 50
    list_filter = (
        "upshelf_time",
        "offshelf_time",
        "category"
    )
    search_fields = ['model_id', 'sale_product', "model_name", 'supplier', 'supplier_name']

    def model_name_display(self, obj):
        return '<p style="width: 30%;">{0}</p>'.format(obj.model_name)

    def supplier_link(self, obj):
        return '<p><a href="/admin/supplier/salesupplier/?id={0}" target="_blank">{1}</a></p>'.format(obj.supplier,
                                                                                                      obj.supplier_name)

    def model_sale_link(self, obj):
        return '<p><a href="/admin/items/product/?model_id={0}" target="_blank">库存款式</a></p></br>' \
               '<p><a href="/admin/supplier/saleproduct/?id={1}" target="_blank">选品款式</a></p>'.format(obj.model_id,
                                                                                                      obj.sale_product)

    def schedule_manager_info(self, obj):
        return '<p><a href="/admin/supplier/saleproductmanage/{0}" target="_blank">具体排期</a></p>' \
               '</br><p>{1}</p></br><p>{2}</p></br>'.format(
            obj.schedule_manage_id,
            obj.upshelf_time,
            obj.offshelf_time)

    def pic_display(self, obj):
        return '<img src="{0}" width="90px" height="150px"/>'.format(obj.pic_url)

    model_name_display.allow_tags = True
    model_name_display.short_description = u'名称'

    pic_display.allow_tags = True
    pic_display.short_description = u'图片'

    schedule_manager_info.allow_tags = True
    schedule_manager_info.short_description = u'排期信息'

    model_sale_link.allow_tags = True
    model_sale_link.short_description = u'款式/选品信息'

    supplier_link.allow_tags = True
    supplier_link.short_description = u'供应商信息'


admin.site.register(ModelStats, ModelStatsAdmin)


class XlmmDailyStatAdmin(admin.ModelAdmin):
    list_display = (
        'total', 'new_join', 'new_pay', 'new_activite', 'new_hasale', 'new_trial', 'new_trial_activite',
        'new_trial_hasale', 'new_task', 'new_lesson', 'new_award', 'date_field', 'created'
    )
    list_per_page = 50
    list_filter = (
        "created",
    )
    search_fields = ['created']


admin.site.register(XlmmDailyStat, XlmmDailyStatAdmin)
