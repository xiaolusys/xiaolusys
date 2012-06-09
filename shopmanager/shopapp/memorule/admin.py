__author__ = 'meixqhi'
from django.contrib import admin
from shopapp.memorule.models import TradeRule



class TradeRuleAdmin(admin.ModelAdmin):
    list_display = ('id','formula','match_tpl_memo','unmatch_tpl_memo','memo','priority','opposite_ids','scope','status')
    list_display_links = ('id','formula','memo')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'modified'
    #ordering = ['created_at']

    list_filter = ('status','scope')
    search_fields = ['memo']


admin.site.register(TradeRule, TradeRuleAdmin)