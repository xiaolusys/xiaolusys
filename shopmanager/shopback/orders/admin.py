from django.contrib import admin
from shopback.orders.models import Order,Trade



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
    list_display = ('id','seller_nick','buyer_nick','type','payment','discount_fee','adjust_fee','post_fee',
                    'total_fee','commission_fee','pay_time','end_time','modified','status')
    list_display_links = ('id','buyer_nick','payment','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter = ('type','status',)
    search_fields = ['id','buyer_nick']


admin.site.register(Trade, TradeAdmin)