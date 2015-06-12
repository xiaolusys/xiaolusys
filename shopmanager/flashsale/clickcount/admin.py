from django.contrib import admin

from .models import ClickCount, WeekCount


class ClickCountAdmin(admin.ModelAdmin):

    list_display = ('linkid', 'weikefu','mobile', 'user_num', 'valid_num', 
                    'click_num','date', 'write_time', 'username')

    list_display_links = ['linkid', 'username']
    list_filter = ('date', 'username')
    date_hierarchy = 'date'
    search_fields = ['=linkid','=mobile']
    
admin.site.register(ClickCount, ClickCountAdmin)

class WeekCountAdmin(admin.ModelAdmin):

    list_display = ('linkid', 'weikefu', 'buyercount', 'user_num', 'valid_num', 'ordernumcount',
                    'conversion_rate', 'week_code', 'write_time')

    list_display_links = ['linkid', 'week_code']
    list_filter = ('week_code',)
    
    search_fields = ['=linkid','=week_code']

admin.site.register(WeekCount, WeekCountAdmin)
