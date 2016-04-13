from django.contrib import admin
from shopapp.autolist.models import Logs, ItemListTask, TimeSlots


class TimeSlotsAdmin(admin.ModelAdmin):
    list_display = ('timeslot',)


admin.site.register(TimeSlots, TimeSlotsAdmin)


class ItemListTaskAdmin(admin.ModelAdmin):
    list_display = ('num_iid', 'list_weekday', 'list_time', 'task_type', 'created_at', 'status')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    # date_hierarchy = 'list_time'
    ordering = ['created_at']

    list_filter = ('status', 'list_weekday', 'list_time', 'task_type')
    search_fields = ['num_iid', 'list_time']
    actions = ['cancleExecute']

    def cancleExecute(self, request, queryset):
        queryset.update(status='delete')

    cancleExecute.short_description = "Cancle Task!"


admin.site.register(ItemListTask, ItemListTaskAdmin)


class ListLogsAdmin(admin.ModelAdmin):
    list_display = (
    'num_iid', 'cat_id', 'cat_name', 'list_weekday', 'list_time', 'num', 'task_type', 'execute_time', 'status')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('task_type', 'list_weekday')
    search_fields = ['cat_name', 'cat_id', 'num_iid', 'list_time']


admin.site.register(Logs, ListLogsAdmin)
