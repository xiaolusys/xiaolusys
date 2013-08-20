#-*- coding:utf8 -*-
from django.contrib import admin
from shopapp.shipclassify.models import ClassifyZone

class ClassifyZoneAdmin(admin.ModelAdmin):
    
    list_display = ('state','city','district','zone','code')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    search_fields = ['state','city','district','zone','code']


admin.site.register(ClassifyZone,ClassifyZoneAdmin)