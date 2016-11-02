# -*- coding:utf8 -*-
from django.contrib import admin
from shopapp.modifyfee.models import FeeRule, ModifyFee


class FeeRuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'discount', 'adjust_fee')
    # list_editable = ('update_time','task_type' ,'is_success','status')
    list_display_links = ('id',)


admin.site.register(FeeRule, FeeRuleAdmin)


class ModifyFeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'tid', 'buyer_nick', 'total_fee', 'payment', 'post_fee', 'modify_fee', 'modified')
    # list_editable = ('update_time','task_type' ,'is_success','status')
    list_display_links = ('id', 'tid',)


admin.site.register(ModifyFee, ModifyFeeAdmin)
