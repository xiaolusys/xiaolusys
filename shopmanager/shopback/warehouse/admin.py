# -*- coding:utf8 -*-
from django.contrib import admin
from .models import WareHouse


class WareHouseAdmin(admin.ModelAdmin):
    list_display = ('id', 'ware_name', 'city', 'address', 'in_active', 'extra_info')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('in_active',)
    search_fields = ['ware_name', 'city']


admin.site.register(WareHouse, WareHouseAdmin)
