# coding: utf-8
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from core.filters import DateScheduleFilter
from .models import ForecastInbound, ForecastInboundDetail, RealInBound, RealInBoundDetail
from supplychain.supplier.models import SaleSupplier
from flashsale.dinghuo.models import OrderList

from core.widgets import AdminTextThumbnailWidget
from .services import strip_forecast_inbound

from core.options import log_action, ADDITION

class ForecastInboundDetailInline(admin.TabularInline):
    model = ForecastInboundDetail

    fields = ('product_img', 'product_id', 'sku_id', 'product_name', 'forecast_arrive_num', 'status')

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ('product_id', 'sku_id', 'product_name','forecast_arrive_num', 'status')
        return self.readonly_fields

    def formfield_for_dbfield(self, db_field, request=None, **kwargs):
        if db_field.name == 'product_img':
            kwargs['widget'] = AdminTextThumbnailWidget(attrs={'width:':80,'height':80})
        return super(ForecastInboundDetailInline, self).formfield_for_dbfield(db_field, **kwargs)

class RealInBoundDetailInline(admin.TabularInline):
    model = RealInBoundDetail

    fields = ( 'product_img','product_id', 'sku_id', 'product_name', 'arrival_quantity', 'inferior_quantity', 'district', 'status')

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ('product_id', 'sku_id', 'product_name',
                                           'arrival_quantity', 'district', 'status')
        return self.readonly_fields

    def formfield_for_dbfield(self, db_field, request=None, **kwargs):
        if db_field.name == 'product_img':
            kwargs['widget'] = AdminTextThumbnailWidget(attrs={'width:':80,'height':80})
        return super(RealInBoundDetailInline, self).formfield_for_dbfield(db_field, **kwargs)


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

    fieldsets = (
        ('基本信息:', {
         'classes': ('expand',),
         'fields': ('supplier', 'relate_order_set', 'ware_house')
        }),
        ('预测到货状态:', {
         'classes': ('expand',),
         'fields': (('express_code', 'express_no', 'forecast_arrive_time'),
                    ('purchaser', 'status', 'is_lackordefect', 'is_overorwrong'))
        })
    )

    actions = ['action_merge_or_split', 'action_strip_inbound']

    def get_form(self, request, obj=None, **kwargs):
        form = super(ForecastInboundAdmin, self).get_form(request, obj=obj, **kwargs)
        if obj and obj.supplier:
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
            return self.readonly_fields + ('status', 'ware_house',
                                           'purchaser', 'status', 'is_lackordefect', 'is_overorwrong')
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if obj and not obj.purchaser:
            obj.purchaser = request.user.username
        obj.save()

    def delete_model(self, request, obj):
        obj.status = obj.ST_CANCELED
        obj.save()

    def action_merge_or_split(self, request, queryset):

        unapproved_qs = queryset.exclude(status__in=(ForecastInbound.ST_DRAFT,ForecastInbound.ST_APPROVED))
        if unapproved_qs.exists():
            self.message_user(request, u"＊＊＊＊＊＊＊＊＊合并拆分预测到货单必须都在草稿或审核状态＊＊＊＊＊＊＊＊＊!")
            return HttpResponseRedirect(request.get_full_path())

        staff_name = request.user.username
        forecast_ids_str = ','.join([str(obj.id) for obj in queryset])
        return HttpResponseRedirect(reverse('forecast_v1:forecastinbound-list') + '?forecast_ids=%s'%(forecast_ids_str))

    action_merge_or_split.short_description = u"合并拆分同供应商记录"

    def action_strip_inbound(self, request, queryset):

        unarrived_qs = queryset.exclude(status=ForecastInbound.ST_ARRIVED)
        if unarrived_qs.exists() :
            self.message_user(request, u"＊＊＊剥离未到货记录订货单需在到货状态＊＊＊!")
            return HttpResponseRedirect(request.get_full_path())

        new_forecast_obj_list = []
        try:
            for obj in queryset:
                new_forecast = strip_forecast_inbound(obj.id)
                log_action(request.user.id, new_forecast, ADDITION, '从预测单(%s)剥离创建'%(obj.id))
                new_forecast_obj_list.append(new_forecast)
        except Exception, exc:
            self.message_user(request, u"剥离出错:%s"%exc.message)
        self.message_user(request, u"＊＊＊到货预测单未到货记录剥离成功,子预测单列表:%s ＊＊＊"%
                          (','.join([str(obj.id) for obj in new_forecast_obj_list ])) )

        return HttpResponseRedirect(request.get_full_path())

    action_strip_inbound.short_description = u"剥离未到货预测记录"


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

    inlines = [RealInBoundDetailInline]

    fieldsets = (
        ('基本信息:', {
            'classes': ('expand',),
            'fields': ('supplier', 'relate_order_set', 'ware_house')
        }),
        ('实际到货状态:', {
            'classes': ('expand',),
            'fields': (('express_code', 'express_no', 'wave_no'),
                       ('creator', 'inspector', 'status'),
                       'memo')
        })
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super(RealInBoundAdmin, self).get_form(request, obj=obj, **kwargs)
        if obj and obj.supplier:
            form.base_fields['supplier'].queryset = form.base_fields['supplier'].queryset.filter(
                id=obj.supplier.id)
            form.base_fields['relate_order_set'].queryset = form.base_fields['relate_order_set'].queryset.filter(
                supplier=obj.supplier).exclude(status=OrderList.SUBMITTING)
        else:
            form.base_fields['supplier'].queryset = form.base_fields['supplier'].queryset\
                .filter(status=SaleSupplier.CHARGED)
            form.base_fields['relate_order_set'].queryset = form.base_fields['relate_order_set'].queryset \
                .exclude(status=OrderList.SUBMITTING)
        return form

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ('status', 'ware_house', 'relate_order_set',
                                           'creator', 'inspector', 'status')
        return self.readonly_fields




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
