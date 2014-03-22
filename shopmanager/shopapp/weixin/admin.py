#-*- coding:utf8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from shopapp.weixin.models import WeiXinAccount,WeiXinUser,WeiXinAutoResponse

class WeiXinAccountAdmin(admin.ModelAdmin):
    
    list_display = ('token','app_id','expires_in','expired','in_voice','is_active')
    
    list_filter = ('is_active','in_voice')
    search_fields = ['app_id','token']
    

admin.site.register(WeiXinAccount, WeiXinAccountAdmin)  


class WeiXinUserAdmin(admin.ModelAdmin):
    
    list_display = ('openid','nickname','sex','province','city','subscribe_time','subscribe')
    
    list_filter = ('subscribe','sex')
    search_fields = ['openid','nickname']
    

admin.site.register(WeiXinUser, WeiXinUserAdmin) 


class WeiXinAutoResponseAdmin(admin.ModelAdmin):
    
    list_display = ('message','rtype','title','content')
    
    list_filter = ('rtype',)
    search_fields = ['message','title','content']
    
    formfield_overrides = {
        models.CharField: {'widget': Textarea(attrs={'rows':5, 'cols':40})},
        models.FloatField: {'widget': TextInput(attrs={'size':'16'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }
    

admin.site.register(WeiXinAutoResponse, WeiXinAutoResponseAdmin) 
