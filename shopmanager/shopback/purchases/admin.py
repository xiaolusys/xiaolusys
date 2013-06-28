#-*- coding:utf8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from shopback import paramconfig as pcfg
from shopback.purchases.models import Purchase,PurchaseItem,\
    PurchaseStorage,PurchaseStorageItem,PurchaseStorageRelate,PurchasePaymentItem

import logging 

logger =  logging.getLogger('purchases.handler')

class PurchaseItemInline(admin.TabularInline):
    
    model = PurchaseItem
    fields = ('supplier_item_id','product','product_sku','purchase_num','discount'
              ,'price','total_fee','payment','status')
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'10'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
        models.FloatField: {'widget': TextInput(attrs={'size':'8'})}
    }
    

class PurchaseStorageItemInline(admin.TabularInline):
    
    model = PurchaseStorageItem
    fields = ('purchase_storage','supplier_item_id','product','product_sku','storage_num','status')
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }


class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id','purchase_title_link','supplier','deposite','purchase_type','total_fee','payment','forecast_date',
                    'post_date','service_date','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('supplier','deposite','purchase_type','status')
    search_fields = ['id','extra_name']
    
    def purchase_title_link(self, obj):
        symbol_link = obj.extra_name or u'【空标题】'

        if  obj.status == pcfg.PURCHASE_DRAFT:
            symbol_link = '<a href="/purchases/%d/" >%s</a>'%(obj.id,symbol_link) 
        return symbol_link
    
    purchase_title_link.allow_tags = True
    purchase_title_link.short_description = "标题"
    
    inlines = [PurchaseItemInline]
    
    
    #--------设置页面布局----------------
    fieldsets =(('采购单信息:', {
                    'classes': ('expand',),
                    'fields': (('supplier','deposite','purchase_type')
                               ,('extra_name','total_fee','payment')
                               ,('forecast_date','service_date','post_date')
                               ,('status','extra_info'))
                }),)
    
    #--------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'16'})},
        models.FloatField: {'widget': TextInput(attrs={'size':'8'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }


admin.site.register(Purchase,PurchaseAdmin)


class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ('id','purchase','product','product_sku','supplier_item_id','purchase_num','discount','price'
                    ,'total_fee','payment','created','modified','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status',)
    search_fields = ['id']

admin.site.register(PurchaseItem,PurchaseItemAdmin)


class PurchaseStorageAdmin(admin.ModelAdmin):
    list_display = ('id','supplier','deposite','purchase_type','forecast_date','post_date','created','modified','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('supplier','deposite','purchase_type','status')
    search_fields = ['id']
    
    inlines = [PurchaseStorageItemInline]

admin.site.register(PurchaseStorage,PurchaseStorageAdmin)


class PurchaseStorageItemAdmin(admin.ModelAdmin):
    list_display = ('id','purchase_storage','supplier_item_id','product','product_sku','storage_num'
                    ,'created','modified','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status',)
    search_fields = ['id']
    
admin.site.register(PurchaseStorageItem,PurchaseStorageItemAdmin)


class PurchaseStorageRelateAdmin(admin.ModelAdmin):
    list_display = ('id','purchase_item','storage_item','relate_num')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    search_fields = ['id']
    

admin.site.register(PurchaseStorageRelate,PurchaseStorageRelateAdmin)


class PurchasePaymentItemAdmin(admin.ModelAdmin):
    list_display = ('id','pay_type','payment','purchase','storage','pay_time','status','extra_info')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status',)
    search_fields = ['id']
    

admin.site.register(PurchasePaymentItem,PurchasePaymentItemAdmin)


