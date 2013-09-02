#-*- coding:utf8 -*-
from django.contrib import admin
from shopapp.shipclassify.models import ClassifyZone,BranchZone

class ClassifyZoneAdmin(admin.ModelAdmin):
    
    list_display = ('state','city','district','zone')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    search_fields = ['state','city','district','zone']


admin.site.register(ClassifyZone,ClassifyZoneAdmin)


class BranchZoneAdmin(admin.ModelAdmin):
    
    list_display = ('code','name','barcode')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    search_fields = ['code','name','barcode']


admin.site.register(BranchZone,BranchZoneAdmin)