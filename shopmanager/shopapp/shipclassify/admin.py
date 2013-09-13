#-*- coding:utf8 -*-
from django.contrib import admin
from shopapp.shipclassify.models import ClassifyZone,BranchZone

class ClassifyZoneInline(admin.TabularInline):
    
    model = ClassifyZone
    fields = ('state','city','district')
    


class ClassifyZoneAdmin(admin.ModelAdmin):
    
    list_display = ('state','city','district','branch')
    list_editable = ('state','city',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    search_fields = ['state','city','district']


admin.site.register(ClassifyZone,ClassifyZoneAdmin)


class BranchZoneAdmin(admin.ModelAdmin):
    
    list_display = ('code','name','barcode')
    list_editable = ('code','name',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    inlines = [ClassifyZoneInline]
    
    search_fields = ['code','name','barcode']


admin.site.register(BranchZone,BranchZoneAdmin)