#-*- coding:utf8 -*-
from django.contrib import admin
from shopapp.smsmgr.models import SMSPlatform,SMSRecord


class SMSPlatformAdmin(admin.ModelAdmin):
    list_display = ('code','name','user_id','account','password','remainums','sendnums','is_default')
    #list_editable = ('update_time','task_type' ,'is_success','status')
    
    list_display_links = ('code','name',)

    search_fields = ['code','name','account']
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = self.readonly_fields+('code',)
        return readonly_fields
    
    
admin.site.register(SMSPlatform,SMSPlatformAdmin)


class SMSRecordAdmin(admin.ModelAdmin):
    list_display = ('id','task_name','task_type','platform','task_id','countnums','succnums','created','modified','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')
    
    list_display_links = ('task_name',)

    list_filter = ('task_type','platform','status',)
    search_fields = ['id','mobiles','task_name',]
    
    
admin.site.register(SMSRecord,SMSRecordAdmin)