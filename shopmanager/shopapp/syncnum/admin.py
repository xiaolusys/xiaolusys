from django.contrib import admin
from shopapp.syncnum.models import ItemNumTask




class ItemNumTaskAdmin(admin.ModelAdmin):
    list_display = ('id','outer_id', 'sku_outer_id', 'num', 'created_at', 'status')
    list_display_links = ('outer_id', 'sku_outer_id')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created_at'
    ordering = ['created_at']

    list_filter = ('status', 'created_at')
    search_fields = ['id','outer_id','sku_outer_id']

    actions = ['cancleExecute']

    def cancleExecute(self, request, queryset):
        queryset.update(status='delete')

    cancleExecute.short_description = "Cancle Task!"


admin.site.register(ItemNumTask, ItemNumTaskAdmin)

