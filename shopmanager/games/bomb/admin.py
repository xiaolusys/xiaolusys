# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import WeixinBomb

class WeixinBombAdmin(admin.ModelAdmin):
    list_display = ('pk','name','contact','mobile','email','qq','numfans','region','category','price','coverage','created')
    
    search_fields = ['name','contact','mobile','email','qq','region','category']
    list_filter = ('region','category')

admin.site.register(WeixinBomb, WeixinBombAdmin) 
