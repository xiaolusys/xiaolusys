__author__ = 'meixqhi'
from django.contrib import admin
from shopapp.memorule.models import TradeRule,RuleFieldType,ProductRuleField,RuleMemo



class TradeRuleAdmin(admin.ModelAdmin):
    list_display = ('id','formula','formula_desc','memo','scope','status')
    list_display_links = ('id','formula','memo')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'modified'
    #ordering = ['created_at']

    list_filter = ('status','scope')
    search_fields = ['memo','formula_desc']


admin.site.register(TradeRule, TradeRuleAdmin)



class RuleFieldTypeAdmin(admin.ModelAdmin):
    list_display = ('field_name','field_type','alias','default_value',)
    list_display_links = ('field_name','field_type')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'modified'
    #ordering = ['created_at']

    list_filter = ('field_type',)
    search_fields = ['field_name']


admin.site.register(RuleFieldType, RuleFieldTypeAdmin)




class ProductRuleFieldAdmin(admin.ModelAdmin):
    list_display = ('id','outer_id','field','custom_alias','custom_default')
    list_display_links = ('id','outer_id')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'modified'
    #ordering = ['created_at']

    list_filter = ('field',)
    search_fields = ['outer_id']


admin.site.register(ProductRuleField, ProductRuleFieldAdmin)




class RuleMemoAdmin(admin.ModelAdmin):
    list_display = ('tid','is_used','rule_memo','seller_flag','created','modified')
    list_display_links = ('tid','rule_memo')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter = ('is_used','seller_flag')
    search_fields = ['tid']


admin.site.register(RuleMemo, RuleMemoAdmin)