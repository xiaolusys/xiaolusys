# -*- coding:utf8 -*-
from django.contrib import admin
from shopback.categorys.models import Category, ProductCategory, CategorySaleStat


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('cid', 'parent_cid', 'name', 'is_parent', 'status', 'sort_order')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status', 'is_parent')
    search_fields = ['cid', 'parent_cid', 'name']


admin.site.register(Category, CategoryAdmin)


class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('cid', 'parent_cid', 'full_name', 'grade', 'is_parent', 'status', 'sort_order')

    # list_editable = ('update_time','task_type' ,'is_success','status')

    def full_name(self, obj):
        return '%s' % obj

    full_name.allow_tags = True
    full_name.short_description = u"全名"

    ordering = ['parent_cid', '-sort_order', ]

    list_filter = ('status', 'is_parent')
    search_fields = ['cid', 'parent_cid', 'name']


admin.site.register(ProductCategory, ProductCategoryAdmin)

from .filters import CategoryFilter


class CategorySaleStatAdmin(admin.ModelAdmin):
    list_display = ("stat_date", "category_show", "sale_amount", "sale_num", "pit_num", "collect_num", "collect_amount",
                    "stock_num", "stock_amount", "refund_num", "refund_amount", "created")

    list_filter = ("created", CategoryFilter, 'stat_date')

    def category_show(self, obj):
        return obj.category_display

    category_show.allow_tags = True
    category_show.short_description = "类别"


admin.site.register(CategorySaleStat, CategorySaleStatAdmin)
