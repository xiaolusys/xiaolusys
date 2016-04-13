# -*- coding:utf8 -*-
from django.contrib import admin
from shopapp.juhuasuan.models import PinPaiTuan


class PinPaiTuanAdmin(admin.ModelAdmin):
    list_display = ('id', 'outer_id', 'outer_sku_id', 'prod_sku_name')
    list_display_links = ('id',)
    # list_editable = ('update_time','task_type' ,'is_success','status')

    search_fields = ['outer_id', 'id', 'outer_sku_id']


admin.site.register(PinPaiTuan, PinPaiTuanAdmin)
