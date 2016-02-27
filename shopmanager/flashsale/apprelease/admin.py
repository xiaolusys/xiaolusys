# coding=utf-8
from django.contrib import admin
from .models import AppRelease


class AppReleaseAdmin(admin.ModelAdmin):
    list_display = ('version', 'status', 'release_time', 'created', 'release_time')
    search_fields = ('version',)
    list_filter = ['created', 'version']


admin.site.register(AppRelease, AppReleaseAdmin)
