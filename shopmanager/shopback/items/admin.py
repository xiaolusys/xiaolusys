from django.contrib import admin
from shopback.items.models import Item,Product,ProductSku



class ItemAdmin(admin.ModelAdmin):
    list_display = ('num_iid','product','category','price','user','title','pic_url')
    list_display_links = ('num_iid', 'title')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'modified'
    #ordering = ['created_at']


    list_filter = ('approve_status',)
    search_fields = ['num_iid', 'title']


admin.site.register(Item, ItemAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('outer_id','name','category','collect_num','price','created','out_stock','modified')
    list_display_links = ('outer_id',)
    list_editable = ('name','collect_num','price')

    date_hierarchy = 'modified'
    #ordering = ['created_at']


    list_filter = ('category',)
    search_fields = ['outer_id', 'name']


admin.site.register(Product, ProductAdmin)


class ProductSkuAdmin(admin.ModelAdmin):
    list_display = ('outer_id','product','quantity','properties_name','properties','out_stock','status')
    list_display_links = ('outer_id',)
    list_editable = ('quantity',)

    #date_hierarchy = 'modified'
    #ordering = ['created_at']


    list_filter = ('status',)
    search_fields = ['outer_id', 'properties_name']


admin.site.register(ProductSku, ProductSkuAdmin)
  