from django.contrib import admin
from shopback.purchases.models import Deposite,PurchaseType,Purchase,PurchaseItem,PurchaseProductSku,PurchaseProduct



class DepositeAdmin(admin.ModelAdmin):
    list_display = ('id','deposite_name','location','in_use','extra_info')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('in_use',)
    search_fields = ['id','deposite_name','location']


admin.site.register(Deposite,DepositeAdmin)


class PurchaseTypeAdmin(admin.ModelAdmin):
    list_display = ('id','type_name','in_use','extra_info')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('in_use',)
    search_fields = ['id','type_name']


admin.site.register(PurchaseType,PurchaseTypeAdmin)


class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id','supplier','deposite','type','forecast_time','post_time','created','modified','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('supplier','deposite','type','status')
    search_fields = ['id']


admin.site.register(Purchase,PurchaseAdmin)


class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ('id','purchase','product','product_sku','supplier_item_id','purchase_num','discount','price'
                    ,'total_fee','payment','created','modified','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status',)
    search_fields = ['id']


admin.site.register(PurchaseItem,PurchaseItemAdmin)

class PurchaseProductAdmin(admin.ModelAdmin):
    list_display = ('id','outer_id','name','category','created','modified','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status',)
    search_fields = ['id','outer_id']


admin.site.register(PurchaseProduct,PurchaseProductAdmin)

class PurchaseProductSkuAdmin(admin.ModelAdmin):
    list_display = ('id','product','outer_id','properties','created','modified','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status',)
    search_fields = ['id','outer_id']


admin.site.register(PurchaseProductSku,PurchaseProductSkuAdmin)
