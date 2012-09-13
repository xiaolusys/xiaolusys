from django.contrib import admin
from shopback.orders.models import Order,Trade



class OrderAdmin(admin.ModelAdmin):
    list_display = ('oid','seller_nick','buyer_nick','trade','price','num_iid','sku_id','num','outer_sku_id','sku_properties_name',
                    'payment','modified','refund_id','is_oversold','refund_status','outer_id','cid','status')
    list_display_links = ('oid','trade','refund_id','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter = ('status','refund_status')
    search_fields = ['oid','buyer_nick','num_iid','sku_properties_name']


admin.site.register(Order, OrderAdmin)




class TradeAdmin(admin.ModelAdmin):
    list_display = ('id','seller_nick','buyer_nick','type','payment','discount_fee','adjust_fee','post_fee','buyer_obtain_point_fee','seller_id',
                    'point_fee','real_point_fee','total_fee','commission_fee','consign_time','pay_time','end_time','modified','shipping_type',
                    'buyer_alipay_no','receiver_name','receiver_mobile','receiver_phone','status')
    list_display_links = ('id','buyer_nick','payment','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'consign_time'
    #ordering = ['created_at']

    list_filter = ('type','status',)
    search_fields = ['id','buyer_nick']


admin.site.register(Trade, TradeAdmin)







