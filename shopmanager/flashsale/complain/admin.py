__author__ = 'timi06'
# -*- coding:utf-8 -*-
from django.contrib import admin
from .models import Complain


class ComplainAdmin(admin.ModelAdmin):
    search_fields = ['id', 'insider_phone']

    list_display = ('com_type', 'insider_phone', 'com_title', 'com_content', 'contact_way', 'created_time',
                    'status', 'custom_serviced', 'reply', 'reply_time')

    list_filter = ['created_time']


admin.site.register(Complain, ComplainAdmin)
