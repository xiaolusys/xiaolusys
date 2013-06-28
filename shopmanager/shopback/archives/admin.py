#-*- coding:utf8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from shopback.archives.models import SupplierType,Supplier,Deposite,PurchaseType,DepositeDistrict

class DepositeDistrictInline(admin.TabularInline):
    
    model = DepositeDistrict
    fields = ('district_no','location','in_use','extra_info')
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }

class DepositeAdmin(admin.ModelAdmin):
    list_display = ('id','deposite_name','location','in_use','extra_info')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    inlines = [DepositeDistrictInline]

    list_filter = ('in_use',)
    search_fields = ['id','deposite_name','location']


admin.site.register(Deposite,DepositeAdmin)


class DepositeDistrictAdmin(admin.ModelAdmin):
    list_display = ('id','deposite','district_no','location','in_use','extra_info')
    #list_editable = ('update_time','task_type' ,'is_success','status')
    
    list_filter = ('in_use',)
    search_fields = ['id','deposite_name','location']


admin.site.register(DepositeDistrict,DepositeDistrictAdmin)


class SupplierTypeAdmin(admin.ModelAdmin):
    list_display = ('id','type_name','extra_info')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    search_fields = ['id','type_name']


admin.site.register(SupplierType,SupplierTypeAdmin)


class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id','supply_type','supplier_name','contact','phone','mobile','fax','zip_code','email'
                    ,'address','account_bank','account_no','main_page','in_use')
    #list_editable = ('update_time','task_type' ,'is_success','status')
    
    list_filter = ('supply_type','in_use',)
    search_fields = ['id','supplier_name']
    
     #--------设置页面布局----------------
    fieldsets =(('供应商基本信息:', {
                    'classes': ('expand',),
                    'fields': (('supplier_name','supply_type')
                               ,('contact','phone')
                               ,('mobile','fax')
                               ,('zip_code','email')
                               ,('address')
                               ,('account_bank','account_no')
                               ,('main_page','in_use')
                               ,'extra_info')
                }),
               )
    

admin.site.register(Supplier,SupplierAdmin)


class PurchaseTypeAdmin(admin.ModelAdmin):
    list_display = ('id','type_name','in_use','extra_info')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('in_use',)
    search_fields = ['id','type_name']


admin.site.register(PurchaseType,PurchaseTypeAdmin)

