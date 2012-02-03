from django.contrib import admin
from shopback.task.models import ItemListTask



class ItemListTaskAdmin(admin.ModelAdmin):
    list_display = ('visitor_id', 'visitor_nick', 'num_iid', 'title', 'num', 'update_time',
                    'task_type' ,'created_at','is_success','status')
    list_display_links = ('num_iid', 'title')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'update_time'
    ordering = ['created_at']

    list_filter = ('is_success', 'update_time')
    search_fields = ['visitor_nick','title']

    actions = ['cancleExecute']

    def cancleExecute(self, request, queryset):
        queryset.update(status=False)

    cancleExecute.short_description = "Cancle the schedule task!"


admin.site.register(ItemListTask, ItemListTaskAdmin)

