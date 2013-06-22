#-*- coding:utf8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from shopback.purchases.models import PurchaseType,Purchase,PurchaseItem,\
    PurchaseStorage,PurchaseStorageItem,PurchaseStorageRelate,PurchasePaymentItem

import logging 

logger =  logging.getLogger('purchases.handler')

class PurchaseItemInline(admin.TabularInline):
    
    model = PurchaseItem
    fields = ('purchase','supplier_item_id','product','product_sku','purchase_num','discount'
              ,'price','total_fee','payment','status')
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }

class PurchaseStorageItemInline(admin.TabularInline):
    
    model = PurchaseStorageItem
    fields = ('purchase_storage','supplier_item_id','product','product_sku','storage_num','status')
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }


class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id','supplier','deposite','purchase_type','total_fee','payment','forecast_date',
                    'post_date','service_date','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('supplier','deposite','purchase_type','status')
    search_fields = ['id']
    
    inlines = [PurchaseItemInline]

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


