#-*- coding:utf8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from shopback.items.models import Item,Product,ProductSku
import logging 

logger =  logging.getLogger('tradepost.handler')

class ProductSkuInline(admin.TabularInline):
    
    model = ProductSku
    fields = ('outer_id','prod_outer_id','purchase_product_sku','quantity','warn_num','remain_num','properties_name','out_stock',
                    'sync_stock','is_assign','status')
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }

class ItemAdmin(admin.ModelAdmin):
    list_display = ('num_iid','product','category','price','user','title','pic_url','last_num_updated')
    list_display_links = ('num_iid', 'title')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'last_num_updated'
    #ordering = ['created_at']


    list_filter = ('user','approve_status')
    search_fields = ['num_iid', 'outer_id', 'title']


admin.site.register(Item, ItemAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('id','outer_id','name','category','collect_num','warn_num','remain_num','price','sync_stock','out_stock','create_date','modify_date','status')
    list_display_links = ('id','outer_id',)
    list_editable = ('name','collect_num')
    
    date_hierarchy = 'modified'
    #ordering = ['created_at']
    
    def create_date(self, obj):
        return obj.created.strftime('%Y-%m-%d %H:%M')

    create_date.short_description = '创建日期'.decode('utf8')
    create_date.admin_order_field = 'created'
    
    def modify_date(self, obj):
        return obj.modified.strftime('%Y-%m-%d %H:%M')
    
    modify_date.short_description = '修改日期'.decode('utf8')
    modify_date.admin_order_field = 'modified'
    
    inlines = [ProductSkuInline]
    
    list_filter = ('status',)
    search_fields = ['outer_id', 'name']


admin.site.register(Product, ProductAdmin)


class ProductSkuAdmin(admin.ModelAdmin):
    list_display = ('id','outer_id','product','quantity','warn_num','remain_num','sync_stock','properties_name','properties','out_stock','modified','status')
    list_display_links = ('outer_id',)
    list_editable = ('quantity',)

    date_hierarchy = 'modified'
    #ordering = ['created_at']
    

    list_filter = ('status',)
    search_fields = ['outer_id', 'properties_name']


admin.site.register(ProductSku, ProductSkuAdmin)
  
