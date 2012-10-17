from django.contrib import admin
from shopback.fenxiao.models import PurchaseOrder,FenxiaoProduct,SubPurchaseOrder

__author__ = 'meixqhi'


class FenxiaoProductAdmin(admin.ModelAdmin):
    list_display = ('pid','name','productcat_id','user','trade_type','standard_price','category','item_id',
                    'cost_price','outer_id','quantity','have_invoice','items_count','orders_count','created','modified','status')
    list_filter = ('user','trade_type','status',)
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    search_fields = ['pid','name']


admin.site.register(FenxiaoProduct, FenxiaoProductAdmin)




class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('fenxiao_id','id','seller_id','supplier_username','distributor_username','logistics_id',
                    'logistics_company_name','trade_type','consign_time','created','pay_time','modified','pay_type','status')
    list_display_links = ('fenxiao_id','id','supplier_username','distributor_username')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter = ('shipping','pay_type','trade_type','status',)
    search_fields = ['fenxiao_id','id','supplier_username','distributor_username']


admin.site.register(PurchaseOrder, PurchaseOrderAdmin)



class SubPurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('fenxiao_id','id','purchase_order','sku_id','tc_order_id','fenxiao_product',
                    'num','price','order_200_status','created','status')
    list_display_links = ('fenxiao_id','id',)
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter = ('order_200_status','status',)
    search_fields = ['fenxiao_id','id','sku_id','title']


admin.site.register(SubPurchaseOrder, SubPurchaseOrderAdmin)



