from django.contrib import admin
from shopapp.syncnum.models import ItemNumTaskLog




class ItemNumTaskLogAdmin(admin.ModelAdmin):
    list_display = ('id','user_id','outer_id', 'sku_outer_id', 'num', 'start_at', 'end_at')
    list_display_links = ('outer_id', 'sku_outer_id')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'end_at'

    list_filter = ('user_id',)
    search_fields = ['id','outer_id','sku_outer_id']

    actions = ['cancleExecute']

    def cancleExecute(self, request, queryset):
        queryset.update(status='delete')

    cancleExecute.short_description = "Cancle Task!"


admin.site.register(ItemNumTaskLog, ItemNumTaskLogAdmin)

