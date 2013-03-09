from django.contrib import admin
from shopback.refunds.models import Refund,RefundProduct

__author__ = 'meixqhi'


class RefundAdmin(admin.ModelAdmin):
    list_display = ('refund_id','tid','oid','num_iid','buyer_nick','total_fee','refund_fee','payment'
                    ,'company_name','sid','has_good_return','created','modified','good_status','order_status','status')
    list_display_links = ('refund_id','tid','buyer_nick')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter   = ('seller_nick','has_good_return','good_status','order_status','status',)
    search_fields = ['refund_id','tid','oid','sid','buyer_nick']


admin.site.register(Refund,RefundAdmin)
  
  
class RefundProductAdmin(admin.ModelAdmin):
    list_display = ('id','outer_id','outer_sku_id','buyer_nick','buyer_mobile','buyer_phone','trade_id'
                    ,'out_sid','company','can_reuse','is_finish','created','modified','memo')
    list_display_links = ('id','outer_id')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter   = ('can_reuse','is_finish')
    search_fields = ['buyer_nick','buyer_mobile','buyer_phone','trade_id','out_sid']


admin.site.register(RefundProduct,RefundProductAdmin)

