# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import PickGroup,WavePick,PickItem,PickPublish

class PickGroupAdmin(admin.ModelAdmin):
    
    list_display = ('name','wave_no','modified','created')
    
    search_fields = ['name','wave_no']

admin.site.register(PickGroup, PickGroupAdmin) 


class WavePickAdmin(admin.ModelAdmin):
    
    list_display = ('wave_no','group_id','out_sid','serial_no','created','status')
    
    search_fields = ['wave_no','group_id','out_sid']

admin.site.register(WavePick, WavePickAdmin) 


class PickItemAdmin(admin.ModelAdmin):
    
    list_display = ('wave_no','serial_no','out_sid','outer_id','outer_sku_id','item_num','barcode')

    search_fields = ['wave_no','out_sid','barcode']

admin.site.register(PickItem, PickItemAdmin) 

class PickPublishAdmin(admin.ModelAdmin):
    
    list_display = ('group_id','pvalue','modified','created')
    
    search_fields = ['group_id',]

admin.site.register(PickPublish,PickPublishAdmin) 

