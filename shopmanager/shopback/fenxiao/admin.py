from django.contrib import admin
from shopback.fenxiao.models import PurchaseOrder

__author__ = 'meixqhi'


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