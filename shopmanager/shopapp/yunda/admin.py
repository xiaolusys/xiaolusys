#-*- coding:utf8 -*-
from django.contrib import admin
from shopapp.yunda.models import ClassifyZone,BranchZone,LogisticOrder

class ClassifyZoneInline(admin.TabularInline):
    
    model = ClassifyZone
    fields = ('state','city','district')
    


class ClassifyZoneAdmin(admin.ModelAdmin):
    
    list_display = ('state','city','district','branch')
    list_display_links = ('state','city',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    search_fields = ['state','city','district']


admin.site.register(ClassifyZone,ClassifyZoneAdmin)


class BranchZoneAdmin(admin.ModelAdmin):
    
    list_display = ('code','name','barcode')
    list_display_links = ('code','name',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    inlines = [ClassifyZoneInline]
    
    search_fields = ['code','name','barcode']


admin.site.register(BranchZone,BranchZoneAdmin)


class LogisticOrderAdmin(admin.ModelAdmin):
    
    list_display = ('cus_oid','out_sid','weight','receiver_name','receiver_state','receiver_city',
                    'receiver_mobile','receiver_phone','created','is_charged','sync_addr','status')
    list_display_links = ('out_sid','cus_oid',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    list_filter = ('status','is_charged','sync_addr')
    search_fields = ['cus_oid','out_sid','receiver_name','receiver_mobile','receiver_phone']


admin.site.register(LogisticOrder,LogisticOrderAdmin)