from django.contrib import admin
from shopback.trades.models import MergeTrade,MergeOrder,MergeBuyerTrade

__author__ = 'meixqhi'


class MergeTradeAdmin(admin.ModelAdmin):
    list_display = ('id','tid','seller_nick','buyer_nick','type','payment','post_fee','total_fee','created','modified',
                    'pay_time','consign_time','receiver_name','status','is_picking_print','out_goods','has_memo'
                    ,'is_express_print','is_send_sms','sys_status')
    list_display_links = ('tid','tid','seller_nick','receiver_name')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter   = ('seller_nick','type','status','sys_status')
    search_fields = ['seller_nick','buyer_nick','tid','receiver_name']


admin.site.register(MergeTrade,MergeTradeAdmin)


class MergeOrderAdmin(admin.ModelAdmin):
    list_display = ('id','tid','oid','seller_nick','buyer_nick','price','num_iid','sku_id','num','outer_sku_id','sku_properties_name',
                    'payment','modified','refund_id','refund_status','outer_id','cid','status')
    list_display_links = ('oid','tid','refund_id','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter = ('seller_nick','status','refund_status')
    search_fields = ['oid','buyer_nick','num_iid','sku_properties_name']


admin.site.register(MergeOrder,MergeOrderAdmin)


class MergeBuyerTradeAdmin(admin.ModelAdmin):
    list_display = ('sub_tid','main_tid','created')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    search_fields = ['sub_tid','main_tid']
    

admin.site.register(MergeBuyerTrade,MergeBuyerTradeAdmin)