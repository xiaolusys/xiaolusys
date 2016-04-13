# -*- coding:utf8 -*-
import json
import time
import datetime
import cStringIO as StringIO
from django.contrib import admin
from django.db import models
from django.contrib import messages
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.forms import TextInput, Textarea
from shopback import paramconfig as pcfg
from shopback.items.models import Product, ProductSku
from core.filters import DateFieldListFilter
from shopback.purchases.models import Purchase, PurchaseItem, PurchaseStorage, \
    PurchaseStorageItem, PurchasePayment, PurchasePaymentItem, PurchaseStorageRelationship
from shopback.purchases import permissions as perms
from common.utils import gen_cvs_tuple, CSVUnicodeWriter, format_date
from core.options import log_action, ADDITION, CHANGE
import logging

logger = logging.getLogger('django.request')


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    fields = ('product_id', 'sku_id', 'outer_id', 'name', 'outer_sku_id', 'properties_name', 'purchase_num',
              'storage_num', 'price', 'std_price', 'total_fee', 'prepay', 'payment',
              'arrival_status', 'status', 'extra_info')

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '20'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
        models.FloatField: {'widget': TextInput(attrs={'size': '8'})}
    }

    def get_readonly_fields(self, request, obj=None):
        if not perms.has_check_purchase_permission(request.user):
            return self.readonly_fields + self.fields[0:-1]
        return self.readonly_fields


class PurchaseStorageItemInline(admin.TabularInline):
    model = PurchaseStorageItem
    fields = ('product_id', 'sku_id', 'outer_id', 'name', 'outer_sku_id', 'properties_name', 'storage_num', 'total_fee',
              'prepay', 'payment', 'is_addon', 'status')

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '20'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }

    def get_readonly_fields(self, request, obj=None):
        if not perms.has_confirm_storage_permission(request.user):
            return self.fields
        return self.readonly_fields


class PurchasePaymentItemInline(admin.TabularInline):
    model = PurchasePaymentItem
    fields = ('product_id', 'sku_id', 'outer_id', 'name', 'outer_sku_id', 'properties_name', 'payment',
              'purchase_id', 'purchase_item_id', 'storage_id', 'storage_item_id')

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '20'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
        models.FloatField: {'widget': TextInput(attrs={'size': '8'})}
    }

    def get_readonly_fields(self, request, obj=None):
        if not perms.has_payment_confirm_permission(request.user):
            return self.readonly_fields + self.fields
        return self.readonly_fields


class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'purchase_title_link', 'origin_no', 'supplier', 'deposite', 'purchase_type'
                    , 'creator', 'receiver_name', 'total_fee', 'prepay', 'payment', 'forecast_date_link',
                    'post_date', 'service_date', 'arrival_status', 'status')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status', 'arrival_status', 'deposite', 'purchase_type',
                   ('service_date', DateFieldListFilter))
    search_fields = ['id', 'origin_no', 'extra_name', 'creator', 'supplier__supplier_name']

    def purchase_title_link(self, obj):
        symbol_link = obj.extra_name or u'【空标题】'

        return '<a href="/purchases/%d/" >%s</a>' % (obj.id, symbol_link)

    purchase_title_link.allow_tags = True
    purchase_title_link.short_description = u"标题"

    def forecast_date_link(self, obj):
        if obj.status == pcfg.PURCHASE_APPROVAL and \
                        (obj.forecast_date - datetime.datetime.now().date()).days < 10 and \
                not obj.storage_num:
            return u'<div style="color:blue;background-color:red;" title="到货日期十日內提示">%s</div>' \
                   % format_date(obj.forecast_date)
        return format_date(obj.forecast_date)

    forecast_date_link.allow_tags = True
    forecast_date_link.short_description = u"预测发货日期"

    inlines = [PurchaseItemInline]

    # --------设置页面布局----------------
    fieldsets = ((u'采购单信息:', {
        'classes': ('expand',),
        'fields': (('supplier', 'deposite', 'purchase_type', 'origin_no', 'extra_name',)
                   , ('total_fee', 'prepay', 'payment', 'prepay_cent')
                   , ('forecast_date', 'service_date', 'post_date')
                   , ('attach_files', 'arrival_status', 'status', 'extra_info'))
    }),)

    # --------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '16'})},
        models.FloatField: {'widget': TextInput(attrs={'size': '8'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }

    def get_readonly_fields(self, request, obj=None):
        if not perms.has_check_purchase_permission(request.user):
            return self.readonly_fields + ('arrival_status', 'total_fee', 'payment', 'status',)
        return self.readonly_fields

    def queryset(self, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = self.model._default_manager.get_queryset()
        # TODO: this should be handled by some parameter to the ChangeList.
        if not request.user.is_superuser:
            qs = qs.exclude(status=pcfg.PURCHASE_INVALID)

        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def addon_cost_action(self, request, queryset):
        """ 更新商品成本 """

        approval_purchases = queryset.filter(status=pcfg.PURCHASE_APPROVAL)
        for purchase in approval_purchases:
            for purchase_item in purchase.effect_purchase_items:
                product_id = purchase_item.product_id
                sku_id = purchase_item.sku_id
                prod = Product.objects.get(outer_id=outer_id)
                if sku_id:
                    prod_sku = ProductSku.objects.get(id=sku_id, product=prod)
                    prod_sku.cost = purchase_item.cost
                    prod_sku.save()
                else:
                    prod.cost = purchase_item.cost
                    prod.save()

            log_action(request.user.id, purchase, CHANGE, u'更新库存商品价格')

        return render_to_response('purchases/purchase_addon_template.html',
                                  {'purchases': approval_purchases},
                                  context_instance=RequestContext(request), content_type="text/html")

    addon_cost_action.short_description = u"更新成本价"

    def invalid_action(self, request, queryset):
        """ 作废采购单 """

        purchase_names = []
        draft_purchases = queryset.filter(status=pcfg.PURCHASE_DRAFT)
        for purchase in draft_purchases:
            purchase.setInvalid()
            purchase_names.append('%d|%s' % (purchase.id, purchase.extra_name))
            log_action(request.user.id, purchase, CHANGE, u'订单作废')

        msg = purchase_names and u'%s 作废成功.' % (','.join(purchase_names)) or '作废失败，请确保订单在草稿状态'

        messages.add_message(request, purchase_names and messages.INFO or messages.ERROR, msg)

        return HttpResponseRedirect('./')

    invalid_action.short_description = u"作废采购单"

    def complete_action(self, request, queryset):
        """ 完成采购单 """

        complete_names = []
        fail_names = []
        approval_purchases = queryset.filter(status=pcfg.PURCHASE_APPROVAL)
        for purchase in approval_purchases:
            if purchase.purchase_num != purchase.storage_num:
                fail_names.append('%d|%s' % (purchase.id, purchase.extra_name))
                continue
            complete_names.append('%d|%s' % (purchase.id, purchase.extra_name))
            purchase.status = pcfg.PURCHASE_FINISH
            purchase.save()
            log_action(request.user.id, purchase, CHANGE, u'采购完成')

        msg = complete_names and u'%s 已完成.' % (','.join(complete_names)) or ''
        msg = '%s%s' % (msg, fail_names and u'%s 未全部到货' % (','.join(fail_names)) or '') or u'采购单需在已审核状态!'
        messages.add_message(request, complete_names and messages.INFO or messages.ERROR, msg)
        return HttpResponseRedirect('./')

    complete_action.short_description = u"完成采购单"

    def export_action(self, request, queryset):
        """ 导出采购单 """

        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') > -1

        pcsv = gen_cvs_tuple(queryset, fields=['id', 'origin_no', 'extra_name', 'purchase_num', 'storage_num',
                                               'total_fee', 'prepay', 'payment', 'supplier', 'service_date', 'created',
                                               'status'],
                             title=[u'ID', u'原单号', u'标题', u'采购数', u'入库数', u'总费用', u'预付款', u'已付款', u'供应商', u'业务日期',
                                    u'创建日期', u'状态'])

        tmpfile = StringIO.StringIO()
        writer = CSVUnicodeWriter(tmpfile, encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)

        response = HttpResponse(tmpfile.getvalue(), content_type='application/octet-stream')
        tmpfile.close()
        response['Content-Disposition'] = 'attachment; filename=purchases-simple-%s.csv' % str(int(time.time()))

        return response

    export_action.short_description = u"导出采购单"

    actions = ['addon_cost_action', 'invalid_action', 'complete_action', 'export_action']


admin.site.register(Purchase, PurchaseAdmin)


# class PurchaseItemAdmin(admin.ModelAdmin):
#    list_display = ('id','purchase','outer_id','name','outer_sku_id','properties_name','purchase_num','price'
#                    ,'total_fee','payment','created','modified','status')
#    #list_editable = ('update_time','task_type' ,'is_success','status')
#
#    list_filter = ('status',)
#    search_fields = ['id']
#
# admin.site.register(PurchaseItem,PurchaseItemAdmin)


class PurchaseStorageAdmin(admin.ModelAdmin):
    list_display = ('id', 'storage_name_link', 'origin_no', 'supplier', 'deposite',
                    'storage_num', 'total_fee', 'prepay', 'payment',
                    'post_date', 'created', 'is_addon', 'status')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status', 'deposite', 'is_addon',
                   ('post_date', DateFieldListFilter),
                   ('created', DateFieldListFilter))
    search_fields = ['id', 'out_sid', 'extra_name', 'origin_no', 'supplier__supplier_name']

    def storage_name_link(self, obj):
        symbol_link = obj.extra_name or u'【空标题】'

        return '<a href="/purchases/storage/%d/" >%s</a>' % (obj.id, symbol_link)

    storage_name_link.allow_tags = True
    storage_name_link.short_description = "标题"

    inlines = [PurchaseStorageItemInline]

    # --------设置页面布局----------------
    fieldsets = (('采购入库单信息:', {
        'classes': ('expand',),
        'fields': (('origin_no', 'supplier', 'deposite', 'extra_name')
                   , ('forecast_date', 'post_date', 'logistic_company', 'out_sid')
                   , ('storage_num', 'total_fee', 'payment', 'is_pod')
                   , ('attach_files', 'status', 'is_addon', 'extra_info'))
    }),)

    # --------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '16'})},
        models.FloatField: {'widget': TextInput(attrs={'size': '8'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }

    def get_readonly_fields(self, request, obj=None):
        if not perms.has_confirm_storage_permission(request.user):
            return self.readonly_fields + ('arrival_status', 'storage_num', 'total_fee', 'payment', 'status',)
        return self.readonly_fields

    def queryset(self, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = self.model._default_manager.get_queryset()
        # TODO: this should be handled by some parameter to the ChangeList.
        if not request.user.is_superuser:
            qs = qs.exclude(status=pcfg.PURCHASE_INVALID)

        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)

        return qs

    def addon_stock_action(self, request, queryset):
        """ 更新库存数 """

        approval_storages = queryset.filter(status__in=(pcfg.PURCHASE_APPROVAL, pcfg.PURCHASE_FINISH))

        for storage in approval_storages:
            not_addon_items = storage.normal_storage_items.filter(is_addon=False)
            if not_addon_items.count() == 0:
                continue

            for storage_item in not_addon_items:
                product_id = storage_item.product_id
                sku_id = storage_item.sku_id
                prod = Product.objects.get(id=product_id)
                if sku_id:
                    prod_sku = ProductSku.objects.get(id=sku_id, product=prod)
                    prod_sku.update_quantity_by_storage_num(storage_item.storage_num)
                else:
                    prod.update_quantity_by_storage_num(storage_item.storage_num)
                storage_item.is_addon = True
                storage_item.save()

            if storage.normal_storage_items.filter(is_addon=False).count() == 0:
                storage.is_addon = True
                storage.save()

            log_action(request.user.id, storage, CHANGE, u'入库单更新到库存')

            for product_id, skus in storage.items_dict.iteritems():
                prod = Product.objects.get(id=product_id)
                log_action(request.user.id, prod, CHANGE, u'入库单(id:%d)更新库存:%s' % (storage.id, json.dumps(skus)))

        addon_storages = queryset.filter(is_addon=True)

        unaddon_storages = queryset.filter(is_addon=False)

        return render_to_response('purchases/storage_addon_template.html',
                                  {'addon_storages': addon_storages, 'unaddon_storages': unaddon_storages},
                                  context_instance=RequestContext(request), content_type="text/html")

    addon_stock_action.short_description = u"更新库存数"

    def invalid_action(self, request, queryset):
        """ 作废入库单 """

        storage_names = []
        draft_storages = queryset.filter(status=pcfg.PURCHASE_DRAFT)
        for storage in draft_storages:
            storage_names.append('%d|%s' % (storage.id, storage.extra_name))
            storage.status = pcfg.PURCHASE_INVALID
            storage.save()
            PurchaseStorageRelationship.objects.filter(storage_id=storage.id).delete()
            log_action(request.user.id, storage, CHANGE, u'订单作废')

        msg = storage_names and u'%s 已作废.' % (','.join(storage_names)) or '作废失败，请确保订单在草稿状态'

        messages.add_message(request, storage_names and messages.INFO or messages.ERROR, msg)
        return HttpResponseRedirect('./')

    invalid_action.short_description = u"作废入库单"

    def complete_action(self, request, queryset):
        """ 完成入库单 """

        storage_names = []
        approval_storages = queryset.filter(status=pcfg.PURCHASE_APPROVAL)
        for storage in approval_storages:
            storage_names.append('%d|%s' % (storage.id, storage.extra_name))
            storage.status = pcfg.PURCHASE_FINISH
            storage.save()
            log_action(request.user.id, storage, CHANGE, u'入库单完成')

        msg = storage_names and u'%s 已完成.' % (','.join(storage_names)) or '作废失败，请确保订单在审核状态.'

        messages.add_message(request, storage_names and messages.INFO or messages.ERROR, msg)
        return HttpResponseRedirect('./')

    complete_action.short_description = u"完成入库单"

    def export_action(self, request, queryset):
        """ 导出入库单 """

        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') > -1

        pcsv = gen_cvs_tuple(queryset, fields=['id', 'origin_no', 'extra_name', 'storage_num',
                                               'total_fee', 'prepay', 'payment', 'supplier', 'is_addon', 'created',
                                               'status'],
                             title=[u'ID', u'原单号', u'标题', u'入库数', u'总费用', u'预付款', u'已付款', u'供应商', u'已入库存', u'创建日期',
                                    u'状态'])

        tmpfile = StringIO.StringIO()
        writer = CSVUnicodeWriter(tmpfile, encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)

        response = HttpResponse(tmpfile.getvalue(), content_type='application/octet-stream')
        tmpfile.close()
        response['Content-Disposition'] = 'attachment;filename=storages-simple-%s.csv' % str(int(time.time()))

        return response

    export_action.short_description = u"导出入库单"

    actions = ['addon_stock_action', 'invalid_action', 'complete_action', 'export_action']


admin.site.register(PurchaseStorage, PurchaseStorageAdmin)


# class PurchaseStorageItemAdmin(admin.ModelAdmin):
#    list_display = ('id','purchase_storage','supplier_item_id','outer_id','name','outer_sku_id',
#                    'properties_name','storage_num','created','modified','status')
#    #list_editable = ('update_time','task_type' ,'is_success','status')
#
#    list_filter = ('status',)
#    search_fields = ['id']
#    
# admin.site.register(PurchaseStorageItem,PurchaseStorageItemAdmin)


class PurchaseStorageRelationshipAdmin(admin.ModelAdmin):
    list_display = ('id', 'purchase_id', 'purchase_item_id', 'storage_id', 'storage_item_id', 'product_id',
                    'sku_id', 'outer_id', 'outer_sku_id', 'is_addon', 'storage_num', 'total_fee', 'payment')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('is_addon',)
    search_fields = ['purchase_id', 'purchase_item_id', 'storage_id', 'outer_id', 'outer_sku_id']


admin.site.register(PurchaseStorageRelationship, PurchaseStorageRelationshipAdmin)


class PurchasePaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'pay_type', 'payment_link', 'applier', 'cashier', 'supplier',
                    'pay_bank', 'pay_no', 'apply_time', 'pay_time', 'status')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status', 'pay_type',
                   ('pay_time', DateFieldListFilter),
                   ('apply_time', DateFieldListFilter))
    search_fields = ['id', 'cashier', 'applier', 'pay_bank', 'pay_no',
                     'supplier__supplier_name', 'origin_nos']

    def payment_link(self, obj):
        symbol_link = obj.payment
        return '<a href="/purchases/payment/distribute/%d/">%s</a>' % (obj.id, symbol_link)

    payment_link.allow_tags = True
    payment_link.short_description = "付款金额"

    fieldsets = (('采购单信息:', {
        'classes': ('expand',),
        'fields': (('pay_type', 'payment', 'pay_no', 'pay_bank', 'supplier')
                   , ('pay_time', 'apply_time', 'applier', 'cashier')
                   , ('origin_nos', 'status', 'extra_info')
                   )
    }),)

    def get_readonly_fields(self, request, obj=None):
        if not perms.has_payment_confirm_permission(request.user):
            return self.readonly_fields + ('pay_type', 'payment', 'pay_no', 'pay_bank', 'pay_time',
                                           'apply_time', 'applier', 'cashier', 'origin_nos', 'status')
        return self.readonly_fields

    inlines = [PurchasePaymentItemInline]

    # --------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '30'})},
        models.FloatField: {'widget': TextInput(attrs={'size': '8'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }

    def queryset(self, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = self.model._default_manager.get_queryset()
        # TODO: this should be handled by some parameter to the ChangeList.
        if not request.user.is_superuser:
            qs = qs.exclude(status=pcfg.PP_INVALID)

        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def invalid_action(self, request, queryset):
        """ 作废付款单 """

        payment_ids = []
        wait_payments = queryset.filter(status__in=(pcfg.PP_WAIT_APPLY, pcfg.PP_WAIT_PAYMENT))
        for payment in wait_payments:
            payment_ids.append('%d|%s' % (payment.id, payment.applier))
            payment.status = pcfg.PP_INVALID
            payment.save()
            log_action(request.user.id, payment, CHANGE, u'付款单作废')

        msg = payment_ids and u'%s 已作废.' % (','.join(payment_ids)) or '作废失败.'

        messages.add_message(request, payment_ids and messages.INFO or messages.ERROR, msg)
        return HttpResponseRedirect('./')

    invalid_action.short_description = u"作废付款单"

    def export_action(self, request, queryset):
        """ 导出付款单 """

        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') > -1

        pcsv = gen_cvs_tuple(queryset, fields=['id', 'pay_type', 'apply_time', 'pay_time',
                                               'payment', 'supplier', 'applier', 'cashier',
                                               'pay_no', 'pay_bank', 'status', 'extra_info'],
                             title=[u'ID', u'付款类型', u'申请时间', u'付款时间', u'付款', u'收款方',
                                    u'申请人', u'付款人', u'流水号', u'支付银行', u'状态', u'备注'])

        tmpfile = StringIO.StringIO()
        writer = CSVUnicodeWriter(tmpfile, encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)

        response = HttpResponse(tmpfile.getvalue(), content_type='application/octet-stream')
        tmpfile.close()
        response['Content-Disposition'] = 'attachment; filename=payment-simple-%s.csv' % str(int(time.time()))

        return response

    export_action.short_description = u"导出付款单"

    actions = ['invalid_action', 'export_action']


admin.site.register(PurchasePayment, PurchasePaymentAdmin)
