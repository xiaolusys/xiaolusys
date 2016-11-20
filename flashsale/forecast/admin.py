# coding: utf-8
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from core.filters import DateScheduleFilter, DateFieldListFilter
from .models import ForecastInbound, ForecastInboundDetail, RealInbound, RealInboundDetail, ForecastStats
from supplychain.supplier.models import SaleSupplier
from flashsale.dinghuo.models import OrderList

from core.widgets import AdminTextThumbnailWidget
from core.admin import BaseAdmin
from .services import strip_forecast_inbound

from core.options import log_action, ADDITION, CHANGE

class ForecastInboundDetailInline(admin.TabularInline):
    model = ForecastInboundDetail

    fields = ('product_img', 'product_id', 'sku_id', 'product_name', 'forecast_arrive_num', 'status')

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ('product_id', 'sku_id', 'product_name','forecast_arrive_num')
        return self.readonly_fields

    def formfield_for_dbfield(self, db_field, request=None, **kwargs):
        if db_field.name == 'product_img':
            kwargs['widget'] = AdminTextThumbnailWidget(attrs={'width:':80,'height':80})
        return super(ForecastInboundDetailInline, self).formfield_for_dbfield(db_field, request=None, **kwargs)

class RealInboundDetailInline(admin.TabularInline):
    model = RealInboundDetail
    fields = ( 'product_img','product_id', 'sku_id', 'product_name',
               'arrival_quantity', 'inferior_quantity', 'district', 'status')

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ('product_id', 'sku_id', 'product_name',
                                           'arrival_quantity', 'district', 'status')
        return self.readonly_fields

    def formfield_for_dbfield(self, db_field, request=None, **kwargs):
        if db_field.name == 'product_img':
            kwargs['widget'] = AdminTextThumbnailWidget(attrs={'width:':80,'height':80})
        return super(RealInboundDetailInline, self).formfield_for_dbfield(db_field, request=None, **kwargs)


STATUS_LABEL_DICT = dict((
    (ForecastInbound.ST_DRAFT, 'label label-info'),
    (ForecastInbound.ST_APPROVED, 'label label-success'),
    (ForecastInbound.ST_ARRIVED, 'label label-primary'),
    (ForecastInbound.ST_TIMEOUT, 'label label-warning'),
    (ForecastInbound.ST_CLOSED, 'label label-danger'),
    (ForecastInbound.ST_CANCELED, 'label label-default'),
    (ForecastInbound.ST_FINISHED, 'label')
))

class ForecastInboundAdmin(BaseAdmin):

    list_display = (
        'id', 'forecast_no', 'supplier', 'ware_house', 'express_no', 'forecast_arrive_time','total_forecast_num',
        'total_arrival_num', 'status_label', 'orderlist_link', 'purchaser', 'has_lack', 'has_defact', 'has_overhead',
        'has_wrong', 'created', 'arrival_time', 'delivery_time'
    )
    list_filter = ('status', 'ware_house', ('created', DateFieldListFilter),
                   ('forecast_arrive_time',DateScheduleFilter),
                   'has_lack', 'has_defact','has_overhead', 'has_wrong')

    search_fields = ['=id', '=forecast_no','=supplier__supplier_name','=express_no','=purchaser','=relate_order_set__id']
    filter_horizontal = ('relate_order_set',)
    save_on_top = True
    list_per_page = 25
    inlines = [ForecastInboundDetailInline]
    fieldsets = (
        ('基本信息:', {
         'classes': ('expand',),
         'fields': ('supplier', 'relate_order_set',('ware_house','status'))
        }),
        ('预测到货状态:', {
         'classes': ('expand',),
         'fields': (('express_code', 'express_no', 'forecast_arrive_time'),
                    ('purchaser', 'has_lack', 'has_defact','has_overhead', 'has_wrong'),
                    'memo')
        })
    )

    def orderlist_link(self, obj):
        order_ids = obj.relate_order_set.values_list('id',flat=True)
        return '<br>'.join(
            ['<a href="/sale/dinghuo/changedetail/%(id)d" target="_blank">%(id)d</a>' % {'id': oid} for oid in order_ids])

    orderlist_link.allow_tags = True
    orderlist_link.short_description = u'订货单ID'

    def status_label(self, obj):
        return '<label class="%s">%s</label>'%(STATUS_LABEL_DICT.get(obj.status), obj.get_status_display())

    status_label.allow_tags = True
    status_label.short_description = u'状态'
    status_label.ordering = 'status'

    actions = ['action_merge_or_split',
               'action_strip_inbound',
               'action_arrival_finished',
               'action_timeout_reforecast',
               'action_close_unarrival',
               'action_purchaseorder_refresh_data']

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
            return self.readonly_fields + ('ware_house', 'forecast_no', 'purchaser',
                                            'has_lack', 'has_defact', 'has_overhead', 'has_wrong')
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if obj and not obj.purchaser:
            obj.purchaser = request.user.username
        obj.save()

    def action_merge_or_split(self, request, queryset):

        unapproved_qs = queryset.exclude(status__in=(ForecastInbound.ST_DRAFT,
                                                     ForecastInbound.ST_APPROVED))
        if unapproved_qs.exists():
            self.message_user(request, u"＊＊＊＊＊＊＊＊＊合并拆分预测到货单必须都在草稿或审核状态＊＊＊＊＊＊＊＊＊!")
            return HttpResponseRedirect(request.get_full_path())

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
                if not new_forecast:
                    continue
                log_action(request.user.id, new_forecast, ADDITION, u'从预测单(%s)剥离创建'%(obj.id))
                new_forecast_obj_list.append(new_forecast)
        except Exception, exc:
            self.message_user(request, u"剥离出错:%s"%exc.message)
        self.message_user(request, u"＊＊＊到货预测单未到货记录剥离成功,子预测单列表:%s ＊＊＊"%
                          (','.join([str(obj.id) for obj in new_forecast_obj_list ])) )

        return HttpResponseRedirect(request.get_full_path())

    action_strip_inbound.short_description = u"剥离未到货预测记录"

    def action_timeout_reforecast(self, request, queryset):

        staging_qs = queryset.filter(status__in=(ForecastInbound.ST_APPROVED, ForecastInbound.ST_DRAFT))
        if not staging_qs.exists():
            self.message_user(request, u"＊＊＊重新预测到货需在草稿或审核状态下处理＊＊＊!")
            return HttpResponseRedirect(request.get_full_path())

        new_forecast_obj_list = []
        try:
            for obj in queryset:
                if not obj.is_arrival_timeout():
                    continue
                new_forecast = strip_forecast_inbound(obj.id)
                if not new_forecast:
                    continue
                log_action(request.user.id, new_forecast, ADDITION, u'超时重新预测到货,原单(id:%s)' % (obj.id))
                new_forecast_obj_list.append(new_forecast)
                new_forecast.memo += u">>> 超时重新预测,上次预测时间:%.19s \n" % obj.forecast_arrive_time
                new_forecast.save(update_fields=['memo'])
                obj.status = ForecastInbound.ST_TIMEOUT
                obj.save(update_fields=['status'])
        except Exception, exc:
            self.message_user(request, u"创建出错:%s" % exc.message)
        if not new_forecast_obj_list:
            self.message_user(request, u"＊＊＊ 没有超时的预测单需要重新预测 ＊＊＊")
        else:
            self.message_user(request, u"＊＊＊超时预测到货单重新预测成功,子预测单列表:%s ＊＊＊" %
                          (','.join([str(obj.id) for obj in new_forecast_obj_list])))

        return HttpResponseRedirect(request.get_full_path())

    action_timeout_reforecast.short_description = u"超时重新预测到货"


    def action_close_unarrival(self, request, queryset):

        unapproved_qs = queryset.filter(status__in=(ForecastInbound.ST_DRAFT,
                                                     ForecastInbound.ST_APPROVED))
        if not unapproved_qs.exists():
            self.message_user(request, u"＊＊＊预测单缺货关闭需在草稿审核状态下处理＊＊＊!")
            return HttpResponseRedirect(request.get_full_path())

        close_forecast_ids = ','.join([str(obj.id) for obj in unapproved_qs])
        for obj in unapproved_qs:
            obj.lackgood_close_update_status()
            obj.save(update_fields=['status'])
            log_action(request.user.id, obj, CHANGE, u'预测单缺货关闭')

        self.message_user(request, u"＊＊＊已关闭缺货预测单列表:%s ＊＊＊" %close_forecast_ids)

        return HttpResponseRedirect(request.get_full_path())

    action_close_unarrival.short_description = u"商家缺货无法到货"


    def action_arrival_finished(self, request, queryset):

        unarrived_qs = queryset.filter(status=ForecastInbound.ST_ARRIVED)
        if not unarrived_qs.exists():
            self.message_user(request, u"＊＊＊预测单缺货关闭需在审核状态下处理＊＊＊!")
            return HttpResponseRedirect(request.get_full_path())

        finished_forecast_ids = ','.join([str(obj.id) for obj in unarrived_qs])
        for obj in unarrived_qs:
            obj.inbound_arrive_confirm_finish()
            obj.save(update_fields=['status'])
            log_action(request.user.id, obj, CHANGE, u'预测单标记已完成')

        self.message_user(request, u"＊＊＊到货已完成预测单列表:%s ＊＊＊" % finished_forecast_ids)

        return HttpResponseRedirect(request.get_full_path())

    action_arrival_finished.short_description = u"到货标记完成"

    def action_purchaseorder_refresh_data(self, request, queryset):

        draft_qs = queryset.filter(status=ForecastInbound.ST_DRAFT)
        if not draft_qs.exists():
            self.message_user(request, u"＊＊＊刷新数据需要在草稿状态下处理＊＊＊!")
            return HttpResponseRedirect(request.get_full_path())

        from flashsale.forecast.apis import orderlist_change_forecastinbound
        finished_forecast_ids = ''
        for obj in draft_qs:
            if obj.relate_order_set.count() > 1:
                self.message_user(request, u"＊＊＊预测单(%s)关联多个订货单，不能刷新!!!＊＊＊" % obj)
                continue
            orderlist = obj.relate_order_set.first()
            orderlist_change_forecastinbound(orderlist)
            log_action(request.user.id, obj, CHANGE, u'预测单数据重新刷新')
            finished_forecast_ids += ', %s'% obj.id

        self.message_user(request, u"＊＊＊已刷新预测单列表:%s ＊＊＊" % finished_forecast_ids)

        return HttpResponseRedirect(request.get_full_path())

    action_purchaseorder_refresh_data.short_description = u"根据订货单刷新预测单"


admin.site.register(ForecastInbound, ForecastInboundAdmin)


class ForecastInboundDetailAdmin(admin.ModelAdmin):

    list_display = (
        'id', 'forecast_inbound', 'product_name', 'product_id', 'forecast_arrive_num'
    )
    list_filter = ('status', ('created', DateFieldListFilter))
    search_fields = ['product_id']


admin.site.register(ForecastInboundDetail, ForecastInboundDetailAdmin)


class RealInboundAdmin(BaseAdmin):
    # fieldsets = ((u'用户信息:', {
    #     'classes': ('expand',),
    #     'fields': ('user', 'group')
    # }),)

    list_display = (
        'id','wave_no','forecast_inbound','supplier', 'ware_house', 'creator', 'inspector',
        'total_inbound_num', 'total_inferior_num', 'created', 'status'
    )
    list_filter = ('status', 'ware_house', ('created', DateFieldListFilter))
    search_fields = ['=id', '=wave_no','^supplier__supplier_name', '=express_no', '=creator','=relate_order_set__id']
    filter_horizontal = ('relate_order_set',)
    list_per_page = 25

    inlines = [RealInboundDetailInline]
    fieldsets = (
        ('基本信息:', {
            'classes': ('expand',),
            'fields': ('supplier', 'relate_order_set', ('forecast_inbound','ware_house'))
        }),
        ('实际到货状态:', {
            'classes': ('expand',),
            'fields': (('express_code', 'express_no', 'wave_no'),
                       ('creator', 'inspector', 'status'),
                       'memo')
        })
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super(RealInboundAdmin, self).get_form(request, obj=obj, **kwargs)
        if obj and obj.supplier:
            form.base_fields['supplier'].queryset = form.base_fields['supplier'].queryset.filter(
                id=obj.supplier.id)
            form.base_fields['relate_order_set'].queryset = form.base_fields['relate_order_set'].queryset.filter(
                supplier=obj.supplier).exclude(status=OrderList.SUBMITTING)
            form.base_fields['forecast_inbound'].queryset = form.base_fields['forecast_inbound'].queryset.filter(
                supplier=obj.supplier)
        else:
            form.base_fields['supplier'].queryset = form.base_fields['supplier'].queryset\
                .filter(status=SaleSupplier.CHARGED)
            form.base_fields['relate_order_set'].queryset = form.base_fields['relate_order_set'].queryset \
                .exclude(status=OrderList.SUBMITTING)
            form.base_fields['forecast_inbound'].queryset = form.base_fields['forecast_inbound'].queryset.none()
        return form

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ('status', 'wave_no', 'ware_house', 'creator', 'inspector', 'status')
        return self.readonly_fields


admin.site.register(RealInbound, RealInboundAdmin)


class RealInboundDetailAdmin(BaseAdmin):
    # fieldsets = ((u'用户信息:', {
    #     'classes': ('expand',),
    #     'fields': ('user', 'group')
    # }),)

    list_display = (
        'id','inbound', 'product_name', 'product_id', 'arrival_quantity', 'inferior_quantity', 'district', 'created', 'status'
    )
    list_filter = ('status', ('created', DateFieldListFilter))
    search_fields = ['inbound' ,'product_id', 'product_name']


admin.site.register(RealInboundDetail, RealInboundDetailAdmin)

class ForecastStatsAdmin(BaseAdmin):

    list_display = (
        'forecast_inbound', 'buyer_name', 'purchaser', 'purchase_num', 'inferior_num', 'lack_num',
        'purchase_amount', 'purchase_time', 'delivery_time', 'arrival_time', 'billing_time', 'finished_time',
        'has_lack', 'has_defact', 'has_overhead', 'has_wrong', 'is_unrecordlogistic', 'is_timeout', 'is_lackclose'
    )
    list_filter = ('buyer_name', 'purchaser', ('purchase_time', DateScheduleFilter),
                   'is_timeout','is_lackclose','is_unrecordlogistic')
    search_fields = ['=forecast_inbound' ,'=supplier__id', '=supplier__supplier_name']

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + ('forecast_inbound','supplier')



admin.site.register(ForecastStats, ForecastStatsAdmin)
