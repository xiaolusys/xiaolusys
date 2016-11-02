# -*- coding: utf-8 -*-
from django.contrib import admin
from core.filters import DateFieldListFilter
from .models import WeixinBomb


class WeixinBombAdmin(admin.ModelAdmin):
    list_display = (
    'pk', 'name', 'creator', 'contact', 'mobile', 'email', 'qq', 'numfans', 'region', 'category', 'price', 'coverage',
    'created')

    search_fields = ['name', 'contact', 'mobile', 'email', 'qq', 'region', 'category', 'creator__username']
    list_filter = ('region', 'category', ('created', DateFieldListFilter), ('modified', DateFieldListFilter))

    # --------设置页面布局----------------
    fieldsets = ((u'客户基本信息:', {
        'classes': ('expand',),
        'fields': (('name', 'contact')
                   , ('phone', 'mobile')
                   , ('email', 'qq')
                   , ('numfans', 'price')
                   , ('region', 'category')
                   , ('coverage', 'payinfo')
                   , ('memo')
                   )}),)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
        obj.save()


admin.site.register(WeixinBomb, WeixinBombAdmin)
