from django.contrib import admin
from shopback.items.models import Item



class ItemAdmin(admin.ModelAdmin):
    list_display = ('num_iid','outer_iid','cid','price','user_id','nick','title','pic_url')
    list_display_links = ('num_iid', 'title','title')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'modified'
    #ordering = ['created_at']

    list_filter = ('approve_status',)
    search_fields = ['num_iid', 'outer_iid', 'title','nick']


admin.site.register(Item, ItemAdmin)
  