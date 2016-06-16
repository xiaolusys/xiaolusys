# coding: utf-8
from django.contrib import admin
from core.filters import DateScheduleFilter
from .models import ForecastInbound, ForecastInboundDetail, RealInBound, RealInBoundDetail
from supplychain.supplier.models import SaleSupplier
from flashsale.dinghuo.models import OrderList

class ForecastInboundDetailInline(admin.TabularInline):
    model = ForecastInboundDetail

    fields = ('product_id', 'sku_id', 'product_name', 'product_img', 'forecast_arrive_num', 'status')

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ('product_id', 'sku_id', 'product_name',
                                           'product_img', 'forecast_arrive_num')
        return self.readonly_fields


class ForecastInboundAdmin(admin.ModelAdmin):
    # fieldsets = ((u'用户信息:', {
    #     'classes': ('expand',),
    #     'fields': ('user', 'group')
    # }),)

    list_display = (
        'id', 'supplier', 'ware_house', 'express_no', 'forecast_arrive_time', 'purchaser', 'status'
    )
    list_filter = ('status', 'ware_house', ('created', DateScheduleFilter),
                   ('forecast_arrive_time',DateScheduleFilter))

    search_fields = ['=id','=supplier__supplier_name']

    filter_horizontal = ('relate_order_set',)

    inlines = [ForecastInboundDetailInline]

    def get_form(self, request, obj=None, **kwargs):
        form = super(ForecastInboundAdmin, self).get_form(request, obj=obj, **kwargs)
        if obj:
            form.base_fields['supplier'].queryset = form.base_fields['supplier'].queryset.filter(
                id=obj.supplier.id)

            form.base_fields['relate_order_set'].queryset = form.base_fields['relate_order_set'].queryset.filter(
                supplier=obj.supplier).exclude(status=OrderList.SUBMITTING)

        else:
            form.base_fields['supplier'].queryset = form.base_fields['supplier'].queryset.filter(
                status=SaleSupplier.CHARGED)

            form.base_fields['relate_order_set'].queryset = form.base_fields['relate_order_set'].queryset\
                .exclude(status=OrderList.SUBMITTING)
        return form

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ('status', 'ware_house', 'relate_order_set',
                                           'purchaser', 'status', 'is_lackordefect', 'is_overorwrong')
        return self.readonly_fields


admin.site.register(ForecastInbound, ForecastInboundAdmin)


class ForecastInboundDetailAdmin(admin.ModelAdmin):
    # fieldsets = ((u'用户信息:', {
    #     'classes': ('expand',),
    #     'fields': ('user', 'group')
    # }),)

    list_display = (
        'id','product_name','product_id','forecast_arrive_num'
    )
    search_fields = ['product_id']


admin.site.register(ForecastInboundDetail, ForecastInboundDetailAdmin)


class RealInBoundAdmin(admin.ModelAdmin):
    # fieldsets = ((u'用户信息:', {
    #     'classes': ('expand',),
    #     'fields': ('user', 'group')
    # }),)

    list_display = (
        'id','wave_no','forecast_inbound','supplier', 'ware_house', 'creator', 'inspector', 'status'
    )
    list_filter = ('status', 'ware_house', ('created', DateScheduleFilter))
    search_fields = ['supplier__name', 'express_no']

    filter_horizontal = ('relate_order_set',)

    def get_form(self, request, obj=None, **kwargs):
        form = super(RealInBoundAdmin, self).get_form(request, obj=obj, **kwargs)
        if obj:
            form.base_fields['supplier'].queryset = form.base_fields['supplier'].queryset.filter(
                id=obj.supplier.id)
            form.base_fields['forecast_inbound'].queryset = form.base_fields['forecast_inbound'].queryset.filter(
                supplier=obj.supplier, id=obj.forecast_inbound.id)
        else:
            form.base_fields['supplier'].queryset = form.base_fields['supplier'].queryset\
                .filter(status=SaleSupplier.CHARGED)
            form.base_fields['forecast_inbound'].queryset = form.base_fields['forecast_inbound'].queryset\
                .filter(supplier=obj.supplier, status=ForecastInbound.ST_APPROVED)
        return form


admin.site.register(RealInBound, RealInBoundAdmin)


class RealInBoundDetailAdmin(admin.ModelAdmin):
    # fieldsets = ((u'用户信息:', {
    #     'classes': ('expand',),
    #     'fields': ('user', 'group')
    # }),)

    list_display = (
        'id','inbound', 'product_name', 'product_id', 'arrival_quantity', 'inferior_quantity', 'district', 'status'
    )
    list_filter = ('status', ('created', DateScheduleFilter))
    search_fields = ['inbound' ,'product_id', 'product_name']


admin.site.register(RealInBoundDetail, RealInBoundDetailAdmin)
