from django.contrib import admin
from shopback.orders.models import Order,Trade,TradeExtraInfo,Logistics,PurchaseOrder,Refund,MonthTradeReportStatus



class OrderAdmin(admin.ModelAdmin):
    list_display = ('oid','trade','price','num_iid','item_meal_id','sku_id','num','outer_sku_id','total_fee','payment','discount_fee',
                    'adjust_fee','sku_properties_name','refund_id','is_oversold','is_service_order','item_meal_name',
                    'pic_path','seller_nick','buyer_nick','refund_status','outer_iid','cid','status')
    list_display_links = ('num_iid','refund_id','status')
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




class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('fenxiao_id','id','seller_id','supplier_username','distributor_username','logistics_id',
                    'logistics_company_name','post_fee','total_fee','shipping','trade_type','tc_order_id'
                    ,'consign_time','created','pay_time','modified','pay_type','alipay_no','status')
    list_display_links = ('fenxiao_id','id','supplier_username','distributor_username')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter = ('shipping','pay_type','trade_type','status',)
    search_fields = ['fenxiao_id','id','supplier_username','distributor_username']


admin.site.register(PurchaseOrder, PurchaseOrderAdmin)



class RefundAdmin(admin.ModelAdmin):
    list_display = ('refund_id','trade','oid','sid','buyer_nick','total_fee','refund_fee','payment','company_name',
                    'has_good_return','created','modified','good_status','order_status','status')
    list_display_links = ('refund_id','trade','buyer_nick','company_name','good_status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter   = ('seller_nick','has_good_return','good_status','order_status','status',)
    search_fields = ['refund_id','oid','sid','buyer_nick']


admin.site.register(Refund,RefundAdmin)



class MonthTradeReportStatusAdmin(admin.ModelAdmin):
    list_display = ('seller_id','year','month','update_order','update_purchase','update_amount','update_logistics','update_refund','created')
    list_display_links = ('seller_id','year','month')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter   = ('seller_id','year','month')
    search_fields = ['seller_id','year','month']


admin.site.register(MonthTradeReportStatus,MonthTradeReportStatusAdmin)