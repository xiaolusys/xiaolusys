#-*- coding:utf8 -*-
from django.contrib import admin
from django.db import models
from shopapp.weixin.models import WeiXinAccount

class WeiXinAccountAdmin(admin.ModelAdmin):
    
    list_display = ('token','app_id','expires_in','expired','in_voice','is_active')
    
    list_filter = ('is_active','in_voice')
    search_fields = ['app_id','token']
    

admin.site.register(WeiXinAccount, WeiXinAccountAdmin)  