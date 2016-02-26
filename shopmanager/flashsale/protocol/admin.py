# -*- coding:utf8 -*-
from django.contrib import admin
from .models import APPFullPushMessge


class APPFullPushMessgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'target_url', 'platform', 'regid', 'created', 'status')
    list_display_links = ('id', 'target_url', )
    search_fields = ['=id', ]
    list_filter = ('platform', 'status')
    list_per_page = 40
    
admin.site.register(APPFullPushMessge, APPFullPushMessgeAdmin)


