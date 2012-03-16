from django.contrib import admin
from autolist.models import ProductItem



class ProductItemAdmin(admin.ModelAdmin):
    list_display = ('num_iid','owner_id','category_id','category_name','list_time','modified','title','num','onsale')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('list_time','onsale','modified')
    search_fields = ['category_name','title']


admin.site.register(ProductItem,ProductItemAdmin)