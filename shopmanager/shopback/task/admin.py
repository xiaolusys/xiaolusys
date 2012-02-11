from django.contrib import admin
from shopback.task.models import ItemListTask,ItemNumTask



class ItemListTaskAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'nick', 'num_iid', 'title', 'num', 'list_time',
                    'task_type' ,'created_at','status')
    list_display_links = ('num_iid', 'title')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'list_time'
    ordering = ['created_at']

    list_filter = ('status', 'list_time')
    search_fields = ['nick','title']

    actions = ['cancleExecute']

    def cancleExecute(self, request, queryset):
        queryset.update(status='delete')

    cancleExecute.short_description = "Cancle Task!"


admin.site.register(ItemListTask, ItemListTaskAdmin)


class ItemNumTaskAdmin(admin.ModelAdmin):
    list_display = ('id','outer_iid', 'sku_outer_id', 'num', 'created_at', 'status')
    list_display_links = ('outer_iid', 'sku_outer_id')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created_at'
    ordering = ['created_at']

    list_filter = ('status', 'created_at')
    search_fields = ['id','outer_iid','sku_outer_id']

    actions = ['cancleExecute']

    def cancleExecute(self, request, queryset):
        queryset.update(status='delete')

    cancleExecute.short_description = "Cancle Task!"


admin.site.register(ItemNumTask, ItemNumTaskAdmin)

