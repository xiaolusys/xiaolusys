# coding=utf-8
from django.contrib.admin import SimpleListFilter
from .models import ProductCategory


class CategoryFilter(SimpleListFilter):
    title = "类别名"
    parameter_name = "category_cid"

    def lookups(self, request, model_admin):
        category_list = []
        categorys = ProductCategory.objects.all()
        for category in categorys:
            category_list.append((str(category.cid), category))
        return tuple(category_list)

    def queryset(self, request, queryset):
        category_cid = self.value()
        if not category_cid:
            return queryset
        else:
            return queryset.filter(category=category_cid)
