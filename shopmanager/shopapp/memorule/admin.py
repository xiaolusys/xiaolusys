#-*- coding:utf8 -*-
__author__ = 'meixqhi'
import time
import cStringIO as StringIO
from django.http import HttpResponse
from django.contrib import admin
from common.utils import CSVUnicodeWriter
from django.db import models
from django.forms import TextInput, Textarea
from shopapp.memorule.models import TradeRule,RuleFieldType,ProductRuleField,RuleMemo,ComposeRule,ComposeItem



class TradeRuleAdmin(admin.ModelAdmin):
    list_display = ('id','formula','formula_desc','memo','scope','status')
    list_display_links = ('id','formula','memo')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'modified'
    #ordering = ['created_at']

    list_filter = ('status','scope')
    search_fields = ['memo','formula_desc']


#admin.site.register(TradeRule, TradeRuleAdmin)



class RuleFieldTypeAdmin(admin.ModelAdmin):
    list_display = ('field_name','field_type','alias','default_value',)
    list_display_links = ('field_name','field_type')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'modified'
    #ordering = ['created_at']

    list_filter = ('field_type',)
    search_fields = ['field_name']


#admin.site.register(RuleFieldType, RuleFieldTypeAdmin)


class ProductRuleFieldAdmin(admin.ModelAdmin):
    list_display = ('id','outer_id','field','custom_alias','custom_default')
    list_display_links = ('id','outer_id')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'modified'
    #ordering = ['created_at']

    list_filter = ('field',)
    search_fields = ['outer_id']


#admin.site.register(ProductRuleField, ProductRuleFieldAdmin)




class RuleMemoAdmin(admin.ModelAdmin):
    list_display = ('tid','is_used','rule_memo','seller_flag','created','modified')
    list_display_links = ('tid','rule_memo')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter = ('is_used','seller_flag')
    search_fields = ['tid']


#admin.site.register(RuleMemo, RuleMemoAdmin)


class ComposeItemInline(admin.TabularInline):
    
    model = ComposeItem
    fields = ('compose_rule','outer_id','outer_sku_id','num','extra_info')
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }
    

class ComposeRuleAdmin(admin.ModelAdmin):
    list_display = ('id','outer_id','outer_sku_id','payment','type','extra_info','created','modified')
    list_display_links = ('id','outer_id')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']
    search_fields = ['id','outer_id','extra_info']
    
    inlines = [ComposeItemInline]
    
    class Media:
        css = {"all": ("admin/css/forms.css","css/admin/dialog.css", "jquery/jquery-ui-1.10.1.css")}
        js = ("script/admin/adminpopup.js","jquery/jquery-ui-1.8.13.min.js",
              "jquery/addons/jquery.upload.js","memorule/js/rule.csvfile.upload.js")

    def export_compose_rule(self,request,queryset):
        
        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') >-1 
        pcsv =[(u'SN',u'商品编码',u'规格编码',u'品名',u'数量')]
        rindex = 0
        
        for rule in queryset:
            pcsv.append(('CR%s'%rindex,rule.outer_id,rule.outer_sku_id,rule.extra_info,str(rule.gif_count)))
            for item in rule.compose_items.all():
                pcsv.append(('',item.outer_id,item.outer_sku_id,item.extra_info,str(item.num)))
            rindex += 1
            
        tmpfile = StringIO.StringIO()
        writer  = CSVUnicodeWriter(tmpfile,encoding= is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)
            
        response = HttpResponse(tmpfile.getvalue(), mimetype='application/octet-stream')
        tmpfile.close()
        response['Content-Disposition'] = 'attachment; filename=compose-rule-%s.csv'%str(int(time.time()))
        
        return response
        
    export_compose_rule.short_description = u"CSV文件导出"
    
    actions = ['export_compose_rule',]
    
    
admin.site.register(ComposeRule, ComposeRuleAdmin)


class ComposeItemAdmin(admin.ModelAdmin):
    list_display = ('id','compose_rule','outer_id','outer_sku_id','num')
    list_display_links = ('id',)
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    search_fields = ['id','outer_id']


admin.site.register(ComposeItem, ComposeItemAdmin)