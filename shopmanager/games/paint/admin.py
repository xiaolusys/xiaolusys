# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import PaintAccount

class PaintAccountAdmin(admin.ModelAdmin):
    
    list_display = ('account_name','password','province','creater_id','created', 'modified', 'status')
    
    search_fields = ['account_name']
    list_filter = ('province','creater_id')

admin.site.register(PaintAccount, PaintAccountAdmin) 

