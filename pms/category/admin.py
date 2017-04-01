# -*- coding:utf-8 -*-
from django.db import models
from django.contrib import admin
from django.forms import TextInput, Textarea

from .models import (
    FirstCategory,
    SecondCategory,
    ThirdCategory,
    FourthCategory,
    FifthCategory,
    SixthCategory,
)


class FifthCategoryInline(admin.TabularInline):
    model = FifthCategory
    fields = ('name', 'code')

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '32'})},
    }


class SixthCategoryInline(admin.TabularInline):
    model = SixthCategory
    fields = ('name', 'code')

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '32'})},
    }


class FirstCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created')
    search_fields = ['name']


admin.site.register(FirstCategory, FirstCategoryAdmin)


class SecondCategoryAdmin(admin.ModelAdmin):
    list_display = ('parent', 'name', 'code', 'created')
    search_fields = ['name']


admin.site.register(SecondCategory, SecondCategoryAdmin)


class ThirdCategoryAdmin(admin.ModelAdmin):
    list_display = ('parent', 'name', 'code', 'created')
    search_fields = ['parent__name', 'name']


admin.site.register(ThirdCategory, ThirdCategoryAdmin)


class FourthCategoryAdmin(admin.ModelAdmin):
    list_display = ('parent', 'name', 'code', 'created')
    search_fields = ['parent__name', 'name']

    inlines = [FifthCategoryInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            kwargs["queryset"] = ThirdCategory.objects.exclude(name__endswith=u'作废')
        return super(FourthCategoryAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(FourthCategory, FourthCategoryAdmin)


class FifthCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'fullname_link', 'created')
    search_fields = ['name', 'parent__name']

    inlines = [SixthCategoryInline]

    def fullname_link(self, obj):
        return '%s | %s' % (str(obj), obj.encoded)

    fullname_link.allow_tags = True
    fullname_link.short_description = u"全称及编码"


admin.site.register(FifthCategory, FifthCategoryAdmin)


class SixthCategoryAdmin(admin.ModelAdmin):
    list_display = ('parent', 'name', 'code', 'created')
    search_fields = ['parent__name', 'name']

# admin.site.register(SixthCategory, SixthCategoryAdmin)


