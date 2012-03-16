from django.contrib import admin
from shopback.orders.models import Order



class OrderAdmin(admin.ModelAdmin):
    list_display = ('oid','title','price','num_iid','item_meal_id','sku_id','num','outer_sku_id','total_fee','payment','discount_fee',
                    'adjust_fee','modified','sku_properties_name','refund_id','is_oversold','is_service_order','item_meal_name',
                    'pic_path','seller_nick','buyer_nick','refund_status','outer_iid','cid','status')
    list_display_links = ('num_iid', 'title','refund_id','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'modified'
    #ordering = ['created_at']

    list_filter = ('status','refund_status')
    search_fields = ['titile', 'oid', 'cid','buyer_nick','item_meal_name']


admin.site.register(Order, OrderAdmin)
  