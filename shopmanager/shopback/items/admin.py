#-*- coding:utf8 -*-
import json
import datetime
from django.contrib import admin
from django.db import models
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.forms import TextInput, Textarea
from shopback.items.models import Item,Product,ProductSku,OnlineProduct,OnlineProductSku
from shopback import paramconfig as pcfg
import logging 

logger =  logging.getLogger('tradepost.handler')

class OnlineProductSkuInline(admin.TabularInline):
    
    model = OnlineProductSku
    fields = ('outer_id','prod_outer_id','purchase_product_sku','warn_num','remain_num','properties_name','out_stock',
                    'sync_stock','is_assign','status')
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }

class ProductSkuInline(admin.TabularInline):
    
    model = ProductSku
    fields = ('product','outer_id','properties','quantity','warn_num',
              'remain_num','wait_post_num','weight','status')
    
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


class OnlineProductAdmin(admin.ModelAdmin):
    list_display = ('id','outer_id','name','category','warn_num','remain_num','price','sync_stock','out_stock','created','modified','status')
    list_display_links = ('id','outer_id',)
    list_editable = ('name',)
    
    date_hierarchy = 'modified'
    #ordering = ['created_at']
    
    inlines = [OnlineProductSkuInline]
    
    list_filter = ('status',)
    search_fields = ['outer_id', 'name']
    
    #更新用户线上商品入库
    def sync_items_stock(self,request,queryset):
        
        from shopapp.syncnum.tasks import updateItemNum
        
        dt   =   datetime.datetime.now()
        sync_items = []
        for prod in queryset:
            pull_dict = {'outer_id':prod.outer_id,'name':prod.name}
            try:
                items = Item.objects.filter(outer_id=prod.outer_id)
                for item in items:
                    updateItemNum(item.user.visitor_id,item.num_iid,dt)
            except Exception,exc:
                pull_dict['success']=False
                pull_dict['errmsg']=exc.message or '%s'%exc  
            else:
                pull_dict['success']=True
            sync_items.append(pull_dict)
       
        return render_to_response('items/product_action.html',{'prods':sync_items,'action_name':u'更新线上库存'},
                                  context_instance=RequestContext(request),mimetype="text/html")
    
    sync_items_stock.short_description = u"同步淘宝线上库存"
    
    #根据线上商品SKU 更新系统商品SKU
    def update_items_sku(self,request,queryset):
        
        from shopback.items.tasks import updateUserProductSkuTask
        sync_items = []
        for prod in queryset:
            pull_dict = {'outer_id':prod.outer_id,'name':prod.name}
            try:
                items = Item.objects.filter(outer_id=prod.outer_id)
                for item in items:
                    Item.get_or_create(item.user.visitor_id,item.num_iid,force_update=True)    
                
                updateUserProductSkuTask(outer_ids=[prod.outer_id])
                item_sku_outer_ids = set()
                items = Item.objects.filter(outer_id=prod.outer_id)
                for item in items:
                    sku_dict = json.loads(item.skus or '{}')
                    if sku_dict:
                        sku_list = sku_dict.get('sku')
                        item_sku_outer_ids.update([ sku.get('outer_id','') for sku in sku_list])
                prod.prod_skus.exclude(outer_id__in=item_sku_outer_ids).update(status=pcfg.REMAIN)
            except Exception,exc:
                pull_dict['success']=False
                pull_dict['errmsg']=exc.message or '%s'%exc  
            else:
                pull_dict['success']=True
            sync_items.append(pull_dict)
       
        return render_to_response('items/product_action.html',{'prods':sync_items,'action_name':u'更新商品SKU'},
                                  context_instance=RequestContext(request),mimetype="text/html")
    
    update_items_sku.short_description = u"更新系统商品SKU"
    
    actions = ['sync_items_stock','update_items_sku']

admin.site.register(OnlineProduct, OnlineProductAdmin)


class OnlineProductSkuAdmin(admin.ModelAdmin):
    list_display = ('id','outer_id','prod_outer_id','product','warn_num','remain_num','sync_stock','properties_name','properties','out_stock','modified','status')
    list_display_links = ('outer_id',)
    list_editable = ('quantity',)

    date_hierarchy = 'modified'
    #ordering = ['created_at']
    

    list_filter = ('status',)
    search_fields = ['outer_id','product__outer_id','properties_name']


admin.site.register(OnlineProductSku, OnlineProductSkuAdmin)
  
  
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id','outer_id','name','category','collect_num','warn_num','remain_num'
                    ,'wait_post_num','weight','created','modified','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status',)
    search_fields = ['id','outer_id']
    
    inlines = [ProductSkuInline]

admin.site.register(Product,ProductAdmin)


class ProductSkuAdmin(admin.ModelAdmin):
    list_display = ('id','product','outer_id','properties','quantity',
                    'warn_num','remain_num','wait_post_num','weight','created','modified','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status',)
    search_fields = ['id','outer_id']
    

admin.site.register(ProductSku,ProductSkuAdmin)

