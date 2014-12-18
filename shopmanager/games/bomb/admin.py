# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import BombOwner, WeixinBomb
from shopback.trades.filters import DateFieldListFilter

class BombOwnerAdmin(admin.ModelAdmin):
    list_display = ('pk','name','contact','mobile','email','qq','created')
    search_fields = ['name','contact','mobile','email','qq']
    list_filter = ('name',('created',DateFieldListFilter),('modified',DateFieldListFilter))
    
admin.site.register(BombOwner, BombOwnerAdmin) 


class WeixinBombAdmin(admin.ModelAdmin):
    list_display = ('pk','name','bomb_owner','numfans','region','price','coverage','created')
    
    search_fields = ['name','account_name','mobile','bomb_owner__name',]
    list_filter = ('region',('created',DateFieldListFilter),('modified',DateFieldListFilter))

admin.site.register(WeixinBomb, WeixinBombAdmin) 
