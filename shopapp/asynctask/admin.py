from django.contrib import admin
from shopapp.asynctask.models import TaobaoAsyncTaskModel, PrintAsyncTaskModel


class TaobaoAsyncTaskModelAdmin(admin.ModelAdmin):
    list_display = (
    'task_id', 'task', 'top_task_id', 'user_id', 'result', 'fetch_time', 'file_path_to', 'create', 'modified', 'params',
    'status')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status', 'user_id')
    search_fields = ['task_id', 'task', 'top_task_id']


admin.site.register(TaobaoAsyncTaskModel, TaobaoAsyncTaskModelAdmin)


class PrintAsyncTaskModelAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'task_type', 'operator', 'created', 'modified', 'status')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('task_type', 'status')
    search_fields = ['task_id', 'operator']


admin.site.register(PrintAsyncTaskModel, PrintAsyncTaskModelAdmin)
