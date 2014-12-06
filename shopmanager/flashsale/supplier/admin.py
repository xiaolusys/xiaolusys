#-*- coding:utf8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from django.http import HttpResponseRedirect
from .models import SaleProduct,SaleSupplier,SaleCategory

class SaleSupplierAdmin(admin.ModelAdmin):
    list_display = ('id','supplier_code','supplier_name','main_page','created','modified')
    list_display_links = ('id','supplier_name')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #list_filter   = ('can_reuse','is_finish')
    search_fields = ['supplier_name','supplier_code']
    
admin.site.register(SaleSupplier,SaleSupplierAdmin)


class SaleCategoryAdmin(admin.ModelAdmin):
    
    list_display = ('id','name','created','modified')
    
    list_display_links = ('id','name')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #list_filter   = ('can_reuse','is_finish')
    search_fields = ['name',]
    
admin.site.register(SaleCategory,SaleCategoryAdmin)


class SaleProductAdmin(admin.ModelAdmin):
    
    list_display = ('outer_id','title','price','sale_supplier','platform','modified')
    list_display_links = ('outer_id','title')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter   = ('sale_supplier','platform')
    search_fields = ['id','title','outer_id']
    
admin.site.register(SaleProduct,SaleProductAdmin)


