# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import PaintAccount


class PaintAccountAdmin(admin.ModelAdmin):
    list_display = (
    'pk', 'account_name', 'password', 'mobile', 'province', 'creater_id', 'created', 'modified', 'status')

    search_fields = ['account_name', 'mobile']
    list_filter = ('province', 'creater_id', 'status')


admin.site.register(PaintAccount, PaintAccountAdmin)
