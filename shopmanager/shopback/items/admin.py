from django.contrib import admin
from shopback.items.models import Item,Product,ProductSku



class ItemAdmin(admin.ModelAdmin):
    list_display = ('num_iid','product','category','price','user','title','pic_url','last_num_updated')
    list_display_links = ('num_iid', 'title')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'last_num_updated'
    #ordering = ['created_at']


    list_filter = ('user','approve_status')
    search_fields = ['num_iid', 'title']


admin.site.register(Item, ItemAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('outer_id','name','category','collect_num','warn_num','remain_num','price','sync_stock','created','out_stock','modified','status')
    list_display_links = ('outer_id',)
    list_editable = ('name','collect_num','price')

    date_hierarchy = 'modified'
    #ordering = ['created_at']


    list_filter = ('status',)
    search_fields = ['outer_id', 'name']


admin.site.register(Product, ProductAdmin)


class ProductSkuAdmin(admin.ModelAdmin):
    list_display = ('outer_id','product','quantity','warn_num','remain_num','sync_stock','properties_name','properties','out_stock','modified','status')
    list_display_links = ('outer_id',)
    list_editable = ('quantity',)

    date_hierarchy = 'modified'
    #ordering = ['created_at']


    list_filter = ('status',)
    search_fields = ['outer_id', 'properties_name']


admin.site.register(ProductSku, ProductSkuAdmin)
  