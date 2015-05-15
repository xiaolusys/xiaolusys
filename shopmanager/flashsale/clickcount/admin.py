from django.contrib import admin

from .models import ClickCount


class ClickCountAdmin(admin.ModelAdmin):

    list_display = ('linkid', 'weikefu','mobile', 'user_num', 'click_num','date', 'write_time', 'username')

    list_display_links = ['linkid', 'username']
    list_filter = ('date', 'username')
    
    search_fields = ['mobile']
    
admin.site.register(ClickCount, ClickCountAdmin)

