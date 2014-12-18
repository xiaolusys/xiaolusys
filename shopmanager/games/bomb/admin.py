# -*- coding: utf-8 -*-
from django.contrib import admin
from shopback.trades.filters import DateFieldListFilter
from .models import WeixinBomb

class WeixinBombAdmin(admin.ModelAdmin):
    list_display = ('pk','name','creator','contact','mobile','email','qq','numfans','region','category','price','coverage','created')
    
    search_fields = ['name','contact','mobile','email','qq','region','category','creator__username']
    list_filter = ('region','category',('created',DateFieldListFilter),('modified',DateFieldListFilter))

admin.site.register(WeixinBomb, WeixinBombAdmin) 
