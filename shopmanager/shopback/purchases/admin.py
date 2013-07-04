#-*- coding:utf8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from shopback import paramconfig as pcfg
from shopback.items.models import Product,ProductSku
from shopback.purchases.models import Purchase,PurchaseItem,\
    PurchaseStorage,PurchaseStorageItem,PurchasePaymentItem

import logging 

logger =  logging.getLogger('purchases.handler')

class PurchaseItemInline(admin.TabularInline):
    
    model = PurchaseItem
    fields = ('supplier_item_id','outer_id','name','outer_sku_id','properties_name','purchase_num','discount'
              ,'price','total_fee','payment','status','extra_info')
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'10'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
        models.FloatField: {'widget': TextInput(attrs={'size':'8'})}
    }

    

class PurchaseStorageItemInline(admin.TabularInline):
    
    model = PurchaseStorageItem
    fields = ('purchase_storage','supplier_item_id','outer_id','name','outer_sku_id','properties_name','storage_num','status')
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }


class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id','purchase_title_link','origin_no','supplier','deposite','purchase_type','receiver_name','total_fee','payment','forecast_date',
                    'post_date','service_date','arrival_status','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status','arrival_status','supplier','deposite','purchase_type')
    search_fields = ['id','origin_no','extra_name']
    
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
                               ,('origin_no','extra_name','total_fee','payment')
                               ,('forecast_date','service_date','post_date')
                               ,('arrival_status','status','extra_info'))
                }),)
    
    #--------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'16'})},
        models.FloatField: {'widget': TextInput(attrs={'size':'8'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }
    

admin.site.register(Purchase,PurchaseAdmin)


class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ('id','purchase','outer_id','name','outer_sku_id','properties_name','purchase_num','price'
                    ,'total_fee','payment','created','modified','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status',)
    search_fields = ['id']

admin.site.register(PurchaseItem,PurchaseItemAdmin)


class PurchaseStorageAdmin(admin.ModelAdmin):
    list_display = ('id','origin_no','supplier','deposite','forecast_date','post_date','created','modified','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status','supplier','deposite','purchase_type')
    search_fields = ['id','out_sid','origin_no']
    
    inlines = [PurchaseStorageItemInline]
    
    #--------设置页面布局----------------
    fieldsets =(('采购入库单信息:', {
                    'classes': ('expand',),
                    'fields': (('origin_no','supplier','deposite')
                               ,('extra_name','total_fee','payment')
                               ,('forecast_date','service_date','post_date')
                               ,('logistic_company','out_sid','status','extra_info'))
                }),)
    
    #--------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'16'})},
        models.FloatField: {'widget': TextInput(attrs={'size':'8'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }

admin.site.register(PurchaseStorage,PurchaseStorageAdmin)


class PurchaseStorageItemAdmin(admin.ModelAdmin):
    list_display = ('id','purchase_storage','supplier_item_id','outer_id','name','outer_sku_id','properties_name','storage_num'
                    ,'created','modified','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status',)
    search_fields = ['id']
    
admin.site.register(PurchaseStorageItem,PurchaseStorageItemAdmin)



class PurchasePaymentItemAdmin(admin.ModelAdmin):
    list_display = ('id','pay_type','payment','purchase','storage','pay_time','status','extra_info')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status',)
    search_fields = ['id']
    

admin.site.register(PurchasePaymentItem,PurchasePaymentItemAdmin)


