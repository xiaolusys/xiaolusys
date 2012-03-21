from django.contrib import admin
from autolist.models import ProductItem,Logs



class ProductItemAdmin(admin.ModelAdmin):
    list_display = ('num_iid','owner_id','category_id','category_name','list_time','modified','title','num','onsale')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('list_time','onsale','modified')
    search_fields = ['category_name','title']


admin.site.register(ProductItem,ProductItemAdmin)

class ListLogsAdmin(admin.ModelAdmin):
    list_display = ('num_iid','cat_id','cat_name','list_weekday','list_time','num','task_type','execute_time','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('task_type','list_weekday','status')
    search_fields = ['cat_name','cat_id','num_iid','list_time']


admin.site.register(Logs,ListLogsAdmin)