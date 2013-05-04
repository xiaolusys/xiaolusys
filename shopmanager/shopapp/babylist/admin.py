#-*- coding:utf8 -*-
from django.contrib import admin
from shopapp.babylist.models import BabyPhone


class BabyPhoneAdmin(admin.ModelAdmin):
    list_display = ('id','sex','father','address','born','code','hospital',)
    list_display_links = ('id',)
    #list_editable = ('update_time','task_type' ,'is_success','status')
    
    list_filter = ('hospital',)
    search_fields = ['father','id','address']
    

admin.site.register(BabyPhone, BabyPhoneAdmin)