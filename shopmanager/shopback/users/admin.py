from django.contrib import admin
from shopback.users.models import User



class UserAdmin(admin.ModelAdmin):
    list_display = ('id','top_session','has_fenxiao','visitor_id','uid','nick','status')
    list_display_links = ('id', 'nick')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'modified'
    #ordering = ['created_at']

    list_filter = ('update_items_datetime','status')
    search_fields = ['nick','craw_keywords','craw_trade_seller_nicks']


admin.site.register(User, UserAdmin)