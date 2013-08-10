from django.contrib import admin
from shopback.categorys.models import Category,ProductCategory



class CategoryAdmin(admin.ModelAdmin):
    list_display = ('cid','parent_cid','name','is_parent','status','sort_order')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status','is_parent')
    search_fields = ['cid','parent_cid','name']


admin.site.register(Category,CategoryAdmin)
  
  
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('cid','parent_cid','name','is_parent','status','sort_order')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status','is_parent')
    search_fields = ['cid','name']


admin.site.register(ProductCategory,ProductCategoryAdmin)