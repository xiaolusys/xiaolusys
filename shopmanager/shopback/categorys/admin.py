#-*- coding:utf8 -*-
from django.contrib import admin
from shopback.categorys.models import Category,ProductCategory



class CategoryAdmin(admin.ModelAdmin):
    list_display = ('cid','parent_cid','name','is_parent','status','sort_order')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status','is_parent')
    search_fields = ['cid','parent_cid','name']


admin.site.register(Category,CategoryAdmin)
  
  
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('cid','parent_cid','full_name','is_parent','status','sort_order')
    #list_editable = ('update_time','task_type' ,'is_success','status')
    
    def full_name(self, obj):
        return '%s'%obj
    
    full_name.allow_tags = True
    full_name.short_description = u"全名"
    
    ordering = ['parent_cid','-sort_order',]
    
    list_filter = ('status','is_parent')
    search_fields = ['cid','parent_cid','name']


admin.site.register(ProductCategory,ProductCategoryAdmin)