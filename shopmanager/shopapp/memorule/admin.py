# -*- coding:utf8 -*-
__author__ = 'meixqhi'
import time
import cStringIO as StringIO
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import admin
from django.contrib import messages
from common.utils import CSVUnicodeWriter
from django.db import models

from django.forms import TextInput, Textarea
from shopback.items.models import Product, ProductSku
from core.options import log_action, ADDITION, CHANGE
from shopapp.memorule.models import (
    TradeRule,
    RuleFieldType,
    ProductRuleField,
    RuleMemo,
    ComposeRule,
    ComposeItem)
from . import forms


class TradeRuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'formula', 'formula_desc', 'memo', 'scope', 'status')
    list_display_links = ('id', 'formula', 'memo')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    # date_hierarchy = 'modified'
    # ordering = ['created_at']

    list_filter = ('status', 'scope')
    search_fields = ['memo', 'formula_desc']


# admin.site.register(TradeRule, TradeRuleAdmin)



class RuleFieldTypeAdmin(admin.ModelAdmin):
    list_display = ('field_name', 'field_type', 'alias', 'default_value',)
    list_display_links = ('field_name', 'field_type')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    # date_hierarchy = 'modified'
    # ordering = ['created_at']

    list_filter = ('field_type',)
    search_fields = ['field_name']


# admin.site.register(RuleFieldType, RuleFieldTypeAdmin)


class ProductRuleFieldAdmin(admin.ModelAdmin):
    list_display = ('id', 'outer_id', 'field', 'custom_alias', 'custom_default')
    list_display_links = ('id', 'outer_id')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    # date_hierarchy = 'modified'
    # ordering = ['created_at']

    list_filter = ('field',)
    search_fields = ['outer_id']


# admin.site.register(ProductRuleField, ProductRuleFieldAdmin)




class RuleMemoAdmin(admin.ModelAdmin):
    list_display = ('tid', 'is_used', 'rule_memo', 'seller_flag', 'created', 'modified')
    list_display_links = ('tid', 'rule_memo')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    # ordering = ['created_at']

    list_filter = ('is_used', 'seller_flag')
    search_fields = ['tid']


# admin.site.register(RuleMemo, RuleMemoAdmin)



class ComposeItemInline(admin.TabularInline):
    model = ComposeItem
    fields = ('compose_rule', 'outer_id', 'outer_sku_id', 'num', 'extra_info')

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '20'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }


class ComposeRuleAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'outer_id', 'outer_sku_id', 'payment', 'type', 'extra_info', 'start_time', 'end_time', 'status', 'created')
    list_display_links = ('id', 'outer_id')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    # ordering = ['created_at']
    list_filter = ('type', 'status')
    search_fields = ['id', 'outer_id', 'seller_id', 'extra_info']

    form = forms.UserForm
    inlines = [ComposeItemInline]

    class Media:
        css = {"all": ("admin/css/forms.css", "css/admin/dialog.css", "jquery/jquery-ui-1.10.1.css")}
        js = ("script/admin/adminpopup.js", "jquery/jquery-ui-1.8.13.min.js",
              "jquery/addons/jquery.upload.js", "memorule/js/rule.csvfile.upload.js")

    def get_readonly_fields(self, request, obj=None):

        if not request.user.is_superuser:
            return self.readonly_fields + ('scb_count', 'status')
        return self.readonly_fields

    def export_compose_rule(self, request, queryset):

        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') > -1
        pcsv = [(u'SN', u'商品编码', u'规格编码', u'品名', u'数量')]
        rindex = 0

        for rule in queryset:
            pcsv.append(('CR%s' % rindex, rule.outer_id, rule.outer_sku_id, rule.extra_info, str(rule.gif_count)))
            for item in rule.compose_items.all():
                pcsv.append(('', item.outer_id, item.outer_sku_id, item.extra_info, str(item.num)))
            rindex += 1

        tmpfile = StringIO.StringIO()
        writer = CSVUnicodeWriter(tmpfile, encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)

        response = HttpResponse(tmpfile.getvalue(), content_type='application/octet-stream')
        tmpfile.close()
        response['Content-Disposition'] = 'attachment; filename=compose-rule-%s.csv' % str(int(time.time()))

        return response

    export_compose_rule.short_description = u"CSV文件导出"

    def active_items(self, rule, splite_enable=True):

        for item in rule.compose_items.all():

            prod_sku = prod = None
            if item.outer_sku_id:
                prod_sku = Product.objects.getProductSkuByOuterid(
                    item.outer_id,
                    item.outer_sku_id)
            else:
                prod = Product.objects.getProductByOuterid(item.outer_id)

            if not prod_sku and not prod:
                raise Exception(u'拆分明细编码错误:(%s,%s)' % (item.outer_id, item.outer_sku_id))

        up_row = 0
        try:
            ComposeRule.objects.get(outer_id=rule.outer_id,
                                    outer_sku_id=rule.outer_sku_id,
                                    status=True)
        except:
            if rule.outer_sku_id:
                up_row = ProductSku.objects.filter(outer_id=rule.outer_sku_id,
                                                   product__outer_id=rule.outer_id).update(is_split=splite_enable)
            else:
                up_row = Product.objects.filter(outer_id=rule.outer_id).update(is_split=splite_enable)

        return up_row

    def errormsg_user(self, request, message):

        messages.error(request, message)

    def batch_activerule_action(self, request, queryset):
        """ 订单规则批量激活 """

        has_error = False
        for rule in queryset:
            try:
                if rule.type in (ComposeRule.RULE_SPLIT_TYPE,
                                 ComposeRule.RULE_GIFTS_TYPE):
                    self.active_items(rule)

                    rule.status = True
                    rule.save()

                    log_action(request.user.id, rule, CHANGE, u'规则激活')
            except Exception, exc:
                has_error = True
                self.errormsg_user(request, exc.message)

        if not has_error:
            self.message_user(request, u"======= 订单规则批量激活成功 =======")

        return HttpResponseRedirect("./")

    batch_activerule_action.short_description = u"批量规则激活"

    def batch_disactiverule_action(self, request, queryset):
        """ 订单规则批量失效"""

        has_error = False
        for rule in queryset:
            try:
                if rule.type in (ComposeRule.RULE_SPLIT_TYPE,
                                 ComposeRule.RULE_GIFTS_TYPE):
                    rule.status = False
                    rule.save()

                    self.active_items(rule, splite_enable=False)

                    log_action(request.user.id, rule, CHANGE, u'规则失效')
            except Exception, exc:
                has_error = True
                self.errormsg_user(request, exc.message)

        if not has_error:
            self.message_user(request, u"======= 订单规则批量失效成功 =======")

        return HttpResponseRedirect("./")

    batch_disactiverule_action.short_description = u"批量规则失效"

    actions = ['batch_activerule_action', 'batch_disactiverule_action', 'export_compose_rule']


admin.site.register(ComposeRule, ComposeRuleAdmin)


class ComposeItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'compose_rule', 'outer_id', 'outer_sku_id', 'num')
    list_display_links = ('id',)
    # list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    # ordering = ['created_at']

    search_fields = ['id', 'outer_id']


admin.site.register(ComposeItem, ComposeItemAdmin)
