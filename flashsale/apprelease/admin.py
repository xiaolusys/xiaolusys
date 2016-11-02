# coding=utf-8
from django.contrib import admin
from .models import AppRelease


class AppReleaseAdmin(admin.ModelAdmin):
    list_display = ('version', 'version_code', 'release_time', 'device_type', 'auto_update', 'status', 'created')
    search_fields = ('version',)
    list_filter = ['created', 'version', 'device_type']


admin.site.register(AppRelease, AppReleaseAdmin)
