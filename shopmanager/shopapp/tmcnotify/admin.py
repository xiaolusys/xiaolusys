#-*- coding:utf8 -*-
from django.contrib import admin
from shopapp.tmcnotify.models import TmcMessage,TmcUser


class TmcMessageAdmin(admin.ModelAdmin):
    list_display = ('id','user_id','topic','pub_app_key','pub_time','created','is_exec')
    #list_editable = ('update_time','task_type' ,'is_success','status')
    

    list_filter = ('is_exec',)
    search_fields = ['id','user_id','topic','pub_app_key']
    
    
admin.site.register(TmcMessage,TmcMessageAdmin)



class TmcUserAdmin(admin.ModelAdmin):
    list_display = ('id','user_id','user_nick','group_name','modified','created','is_valid')
    #list_editable = ('update_time','task_type' ,'is_success','status')
    

    list_filter = ('is_valid',)
    search_fields = ['id','user_id','user_nick','group_name']
    
    
admin.site.register(TmcUser,TmcUserAdmin)
