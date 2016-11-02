# coding: utf-8
from django.contrib import admin
from .models import SampleProduct, SampleProductSku, ScanLinShi, SampleScan


# Register your models here.

class SampleProductSkuTabularInline(admin.TabularInline):
    model = SampleProductSku


class SampleProductAdmin(admin.ModelAdmin):
    inlines = [SampleProductSkuTabularInline]

    # 获取当前登录人名字
    def save_model(self, request, obj, form, change):
        if obj.buyer == u'':
            obj.buyer = request.user.username
        obj.last_edit_user = request.user.username
        obj.save()

    search_fields = ['id', 'outer_id']

    list_display = ('outer_id', 'title', 'pic_path', 'supplier', 'buyer', 'num', 'status')

    # --------设置页面布局----------------
    fieldsets = (('商品基本信息:', {
        'classes': ('expand',),
        'fields': (('outer_id', 'title', 'pic_path'), ('supplier', 'status'),)
    }),
                 ('必要时可更改信息:', {
                     'classes': ('collapse',),
                     'fields': (('num', 'payment', 'buyer'),)
                 }),)


admin.site.register(SampleProduct, SampleProductAdmin)


class ScanLinShiAdmin(admin.ModelAdmin):
    list_display = ('title', 'sku_name', 'bar_code', 'scan_num', 'scan_type', 'status')


admin.site.register(ScanLinShi)


class SampleScanAdmin(admin.ModelAdmin):
    search_fields = ['id', 'bar_code']

    list_display = ('bar_code', 'pid', 'sku_id', 'title', 'sku_name', 'scan_num', 'scan_type', 'created', 'status')

    list_filter = ['created']

    # 过滤..非超级管理员只能查看状态为已确认的
    def queryset(self, request):  # 重写queryset方法
        qs = super(SampleScanAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(status=1)


admin.site.register(SampleScan, SampleScanAdmin)
