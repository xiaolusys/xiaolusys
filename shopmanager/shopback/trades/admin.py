from django.contrib import admin
from shopback.trades.models import MergeTrade,MergeBuyerTrade

__author__ = 'meixqhi'


class MergeTradeAdmin(admin.ModelAdmin):
    list_display = ('tid','seller_nick','buyer_nick','type','payment','post_fee','total_fee','created','modified',
                    'pay_time','consign_time','receiver_name','status','is_picking_print','reverse_audit_times'
                    ,'is_express_print','is_send_sms','sys_status')
    list_display_links = ('tid','tid','seller_nick','receiver_name')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'modified'
    #ordering = ['created_at']

    list_filter   = ('seller_nick','type','status','sys_status')
    search_fields = ['seller_nick','buyer_nick','tid','receiver_name']


admin.site.register(MergeTrade,MergeTradeAdmin)


class MergeBuyerTradeAdmin(admin.ModelAdmin):
    list_display = ('sub_tid','main_tid','created')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    search_fields = ['sub_tid','main_tid']
    

admin.site.register(MergeBuyerTrade,MergeBuyerTradeAdmin)