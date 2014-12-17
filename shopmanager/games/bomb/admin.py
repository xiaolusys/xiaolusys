# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import BombOwner, WeixinBomb

class BombOwnerAdmin(admin.ModelAdmin):
    list_display = ('pk','name','contact','mobile','email','qq','created')
    search_fields = ['name','contact','mobile','email','qq']

admin.site.register(BombOwner, BombOwnerAdmin) 


class WeixinBombAdmin(admin.ModelAdmin):
    list_display = ('pk','name','numfans','region','price','coverage','created')
    
    search_fields = ['account_name','mobile']
    list_filter = ('region',)

admin.site.register(WeixinBomb, WeixinBombAdmin) 
