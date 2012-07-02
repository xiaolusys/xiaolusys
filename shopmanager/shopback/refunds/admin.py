from django.contrib import admin
from shopback.refunds.models import Refund

__author__ = 'meixqhi'


class RefundAdmin(admin.ModelAdmin):
    list_display = ('refund_id','tid','oid','sid','num_iid','buyer_nick','total_fee','refund_fee','payment','company_name',
                    'has_good_return','created','modified','good_status','order_status','status')
    list_display_links = ('refund_id','tid','buyer_nick','company_name','good_status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter   = ('seller_nick','has_good_return','good_status','order_status','status',)
    search_fields = ['refund_id','oid','sid','buyer_nick']


admin.site.register(Refund,RefundAdmin)
  