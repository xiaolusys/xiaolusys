from django.contrib import admin

from .models import ClickCount


class ClickCountAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'nop', 'frequency', 'date', 'write_time', 'administrator')
    list_display_links = ['number', 'administrator']
    list_filter = ('name', 'nop', 'frequency', 'date', 'write_time', 'administrator')
    search_fields = ['name', 'administrator', 'date']


admin.site.register(ClickCount, ClickCountAdmin)