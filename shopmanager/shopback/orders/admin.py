from django.contrib import admin
from shopback.orders.models import Order,Trade,Logistics



class OrderAdmin(admin.ModelAdmin):
    list_display = ('oid','price','num_iid','item_meal_id','sku_id','num','outer_sku_id','total_fee','payment','discount_fee',
                    'adjust_fee','sku_properties_name','refund_id','is_oversold','is_service_order','item_meal_name',
                    'pic_path','seller_nick','buyer_nick','refund_status','outer_iid','cid','status')
    list_display_links = ('num_iid','refund_id','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'modified'
    #ordering = ['created_at']

    list_filter = ('status','refund_status')
    search_fields = ['titile','buyer_nick','item_meal_name']


admin.site.register(Order, OrderAdmin)




class TradeAdmin(admin.ModelAdmin):
    list_display = ('id','seller_nick','buyer_nick','type','payment','discount_fee','adjust_fee','post_fee','buyer_obtain_point_fee',
                    'point_fee','real_point_fee','total_fee','commission_fee','is_update_amount','consign_time','pay_time','end_time','modified','status')
    list_display_links = ('id','buyer_nick','payment','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter = ('type','is_update_amount','status',)
    search_fields = ['id','buyer_nick']


admin.site.register(Trade, TradeAdmin)




class LogisticsAdmin(admin.ModelAdmin):
    list_display = ('tid','out_sid','company_name','seller_id','seller_nick','buyer_nick','delivery_start','delivery_end'
                    ,'receiver_name','created','modified','type','freight_payer','seller_confirm','status')
    list_display_links = ('tid','buyer_nick','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter = ('seller_nick','freight_payer','seller_confirm','type','status',)
    search_fields = ['tid','out_sid','buyer_nick','receiver_name']


admin.site.register(Logistics, LogisticsAdmin)