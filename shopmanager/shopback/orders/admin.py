from django.contrib import admin
from shopback.orders.models import Order,Trade,TradeExtraInfo



class OrderAdmin(admin.ModelAdmin):
    list_display = ('oid','trade','price','item','item_meal_id','sku_id','num','outer_sku_id','total_fee','payment','discount_fee',
                    'adjust_fee','sku_properties_name','refund_id','is_oversold','is_service_order','item_meal_name',
                    'pic_path','seller_nick','buyer_nick','refund_status','outer_id','cid','status')
    list_display_links = ('refund_id','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'modified'
    #ordering = ['created_at']

    list_filter = ('status','refund_status')
    search_fields = ['buyer_nick','item_meal_name']


admin.site.register(Order, OrderAdmin)




class TradeAdmin(admin.ModelAdmin):
    list_display = ('id','seller_nick','buyer_nick','type','payment','discount_fee','adjust_fee','post_fee','buyer_obtain_point_fee','seller_id',
                    'point_fee','real_point_fee','total_fee','commission_fee','consign_time','pay_time','end_time','modified','shipping_type',
                    'buyer_alipay_no','receiver_name','receiver_mobile','receiver_phone','status')
    list_display_links = ('id','buyer_nick','payment','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter = ('type','status',)
    search_fields = ['id','buyer_nick']


admin.site.register(Trade, TradeAdmin)



class TradeExtraInfoAdmin(admin.ModelAdmin):
    list_display = ('tid','is_update_amount','is_picking_print','is_send_sms','modified','seller_memo')
    list_display_links = ('tid',)
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'modified'

    list_filter = ('is_update_amount','is_picking_print','is_send_sms')
    search_fields = ['tid',]


admin.site.register(TradeExtraInfo, TradeExtraInfoAdmin)



