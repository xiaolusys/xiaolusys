from django.contrib import admin
from shopback.categorys.models import Category



class CategoryAdmin(admin.ModelAdmin):
    list_display = ('cid','parent_cid','name','is_parent','status','sort_order')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status','is_parent')
    search_fields = ['cid','name']


admin.site.register(Category,CategoryAdmin)
  