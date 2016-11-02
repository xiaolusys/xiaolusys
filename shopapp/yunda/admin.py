# -*- coding:utf8 -*-
import time
import datetime
import cStringIO as StringIO
from django.contrib import admin
from django.http import HttpResponse
from shopapp.yunda.models import (ClassifyZone,
                                  BranchZone,
                                  LogisticOrder,
                                  YundaCustomer,
                                  ParentPackageWeight,
                                  TodaySmallPackageWeight,
                                  TodayParentPackageWeight)
from core.filters import DateFieldListFilter
from django.contrib import messages

from .forms import YundaCustomerForm
from .service import YundaService, YundaPackageService, WEIGHT_UPLOAD_LIMIT
from common.utils import gen_cvs_tuple, CSVUnicodeWriter


class ClassifyZoneInline(admin.TabularInline):
    model = ClassifyZone
    fields = ('state', 'city', 'district')


class ClassifyZoneAdmin(admin.ModelAdmin):
    list_display = ('state', 'city', 'district', 'branch')
    list_display_links = ('state', 'city',)

    # date_hierarchy = 'created'
    # ordering = ['created_at']

    search_fields = ['state', 'city', 'district']


admin.site.register(ClassifyZone, ClassifyZoneAdmin)


class BranchZoneAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'barcode')
    list_display_links = ('code', 'name',)

    # date_hierarchy = 'created'
    # ordering = ['created_at']

    inlines = [ClassifyZoneInline]

    search_fields = ['code', 'name', 'barcode']

    def export_branch_zone(self, request, queryset):
        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') > -1
        pcsv = []
        bz_tuple = gen_cvs_tuple(queryset,
                                 fields=['barcode', 'name', 'code'],
                                 title=[u'网点条码', u'网点名称', u'网点编号'])

        tmpfile = StringIO.StringIO()
        writer = CSVUnicodeWriter(tmpfile, encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(bz_tuple)

        response = HttpResponse(tmpfile.getvalue(), content_type='application/octet-stream')
        tmpfile.close()
        response['Content-Disposition'] = 'attachment; filename=branch-zone-%s.csv' % str(int(time.time()))

        return response

    export_branch_zone.short_description = u"导出CSV文件"

    actions = ['export_branch_zone', ]


admin.site.register(BranchZone, BranchZoneAdmin)


class YundaCustomerAdmin(admin.ModelAdmin):
    list_display = (
    'cus_id', 'name', 'ware_by', 'code', 'company_name', 'qr_id', 'lanjian_id', 'ludan_id', 'sn_code', 'device_code',
    'contacter', 'mobile', 'on_qrcode', 'on_lanjian', 'on_ludan', 'on_bpkg', 'status', 'memo')
    list_display_links = ('name', 'company_name',)

    # date_hierarchy = 'created'
    # ordering = ['created_at']
    form = YundaCustomerForm
    list_filter = ('status',)
    search_fields = ['cus_id', 'name', 'code', 'sync_addr', 'company_name', 'contacter']

    # --------设置页面布局----------------
    fieldsets = ((u'客户基本信息:', {
        'classes': ('expand',),
        'fields': (('name', 'code', 'ware_by', 'company_name')
                   , ('company_trade', 'cus_id', 'contacter',)
                   , ('state', 'city', 'district')
                   , ('address', 'zip', 'mobile',)
                   , ('phone', 'status', 'memo')
                   )
    }),
                 (u'二维码设置:', {
                     'classes': ('collapse',),
                     'fields': (('qr_id', 'qr_code', 'on_qrcode'),)
                 }),
                 (u'揽件设置:', {
                     'classes': ('collapse',),
                     'fields': (('lanjian_id', 'lanjian_code', 'sn_code')
                                , ('device_code', 'on_lanjian', 'on_bpkg'))
                 }),
                 (u'录单设置:', {
                     'classes': ('collapse',),
                     'fields': (('ludan_id', 'ludan_code', 'on_ludan'),)
                 })
                 )


admin.site.register(YundaCustomer, YundaCustomerAdmin)


class ParentPackageWeightAdmin(admin.ModelAdmin):
    list_display = ('parent_package_id', 'weight', 'upload_weight', 'weighted', 'uploaded'
                    , 'destinate', 'is_jzhw', 'is_charged')
    list_display_links = ('parent_package_id',)

    # date_hierarchy = 'created'
    # ordering = ['created_at']

    list_filter = ('is_jzhw', 'is_charged', ('weighted', DateFieldListFilter),
                   ('uploaded', DateFieldListFilter))
    search_fields = ['parent_package_id', 'destinate']


admin.site.register(ParentPackageWeight, ParentPackageWeightAdmin)


class TodaySmallPackageWeightAdmin(admin.ModelAdmin):
    list_display = ('package_id', 'parent_package_id', 'weight', 'upload_weight', 'weighted', 'is_jzhw')
    list_display_links = ('package_id', 'parent_package_id',)

    # date_hierarchy = 'created'
    # ordering = ['created_at']

    list_filter = ('is_jzhw',)
    search_fields = ['package_id', 'parent_package_id']

    def package_id_link(self, obj):
        if obj.weight and float(obj.weight) > 3:
            return u'<a href="%s/" style="color:blue;background-color:red;">%s</a>' % \
                   (obj.package_id, obj.package_id)
        return u'<a href="%s/">%s</a>' % (obj.package_id, obj.package_id)

    package_id_link.allow_tags = True
    package_id_link.short_description = u"运单编号"

    class Media:
        css = {"all": ("admin/css/forms.css", "css/admin/dialog.css", "jquery/jquery-ui-1.10.1.css")}
        js = ("script/admin/adminpopup.js", "jquery/jquery-ui-1.8.13.min.js",
              "jquery/addons/jquery.upload.js", "yunda/js/package.csvfile.upload.js")

    def calcPackageWeightAction(self, request, queryset):

        package_service = YundaPackageService()

        for tspw in queryset:
            try:
                weight_tuple = package_service.calcSmallPackageWeight(tspw)
            except Exception, exc:
                messages.warning(request, exc.message)
            else:
                if weight_tuple[0] > 10:
                    messages.warning(request, u'小包（%s）重量超过10公斤,请核实！' % tspw.package_id)

                tspw.weight = weight_tuple[0]
                tspw.upload_weight = weight_tuple[1]
                tspw.save()

    calcPackageWeightAction.short_description = u"计算小包重量"

    def uploadPackageWeightAction(self, request, queryset):

        try:
            package_service = YundaPackageService()

            package_service.uploadSmallPackageWeight(queryset)

        except Exception, exc:
            messages.warning(request, exc.message)
        else:
            messages.info(request, u'上传成功！')

    uploadPackageWeightAction.short_description = u"上传小包重量"

    actions = ['calcPackageWeightAction', 'uploadPackageWeightAction']


admin.site.register(TodaySmallPackageWeight, TodaySmallPackageWeightAdmin)


class TodayParentPackageWeightAdmin(admin.ModelAdmin):
    list_display = ('parent_package_id', 'weight', 'upload_weight', 'weighted', 'is_jzhw')
    list_display_links = ('parent_package_id',)

    # date_hierarchy = 'created'
    # ordering = ['created_at']

    list_filter = ('is_jzhw',)
    search_fields = ['parent_package_id', ]

    class Media:
        css = {"all": ("admin/css/forms.css", "css/admin/dialog.css", "jquery/jquery-ui-1.10.1.css")}
        js = ("script/admin/adminpopup.js", "jquery/jquery-ui-1.8.13.min.js",
              "jquery/addons/jquery.upload.js", "yunda/js/package.csvfile.upload.js")


        # 取消该商品缺货订单

    def calcPackageWeightAction(self, request, queryset):

        package_service = YundaPackageService()

        for bpkw in queryset:
            try:
                weight_tuple = package_service.calcParentPackageWeight(bpkw)
            except Exception, exc:
                messages.warning(request, exc.message)
            else:
                if weight_tuple[0] > 50:
                    messages.error(request, u'集包号(%s)重量异常(%s)，请核实。' %
                                   (bpkw.parent_package_id, weight_tuple[0]))
                    continue

                bpkw.weight = weight_tuple[0]
                bpkw.upload_weight = weight_tuple[1]
                bpkw.save()

    calcPackageWeightAction.short_description = u"计算大包重量"

    def uploadPackageWeightAction(self, request, queryset):

        try:
            package_service = YundaPackageService()

            package_service.uploadParentPackageWeight(queryset)

        except Exception, exc:
            messages.warning(request, exc.message)
        else:
            messages.info(request, u'上传成功！')

    uploadPackageWeightAction.short_description = u"上传大包重量"

    actions = ['calcPackageWeightAction', 'uploadPackageWeightAction']


admin.site.register(TodayParentPackageWeight, TodayParentPackageWeightAdmin)


class LogisticOrderAdmin(admin.ModelAdmin):
    list_display = ('cus_oid', 'out_sid', 'weight', 'receiver_name', 'receiver_state', 'receiver_city',
                    'receiver_mobile', 'weighted', 'created', 'is_charged', 'sync_addr', 'status')  # ,'customer'
    list_display_links = ('out_sid', 'cus_oid',)

    # date_hierarchy = 'created'
    # ordering = ['created_at']

    list_filter = (
    'status', 'is_charged', 'sync_addr', ('weighted', DateFieldListFilter), ('created', DateFieldListFilter))
    search_fields = ['cus_oid', 'out_sid', 'parent_package_id', 'receiver_mobile', 'wave_no']

    class Media:
        css = {"all": ("admin/css/forms.css", "css/admin/dialog.css", "jquery/jquery-ui-1.10.1.css")}
        js = ("script/admin/adminpopup.js", "jquery/jquery-ui-1.8.13.min.js",
              "jquery/addons/jquery.upload.js", "yunda/js/yundaorder.csvfile.upload.js")

    # --------设置页面布局----------------
    fieldsets = ((u'系统信息:', {
        'classes': ('expand',),
        'fields': (('cus_oid', 'yd_customer', 'out_sid', 'parent_package_id',)
                   , ('weight', 'upload_weight', 'weighted', 'uploaded')
                   , ('valid_code', 'dc_code', 'is_charged', 'sync_addr', 'status')
                   )
    }),
                 (u'包裹地址信息:', {
                     'classes': ('expand',),
                     'fields': (('receiver_name', 'receiver_state', 'receiver_city', 'receiver_district'),
                                ('receiver_address', 'receiver_zip', 'receiver_mobile', 'receiver_phone', 'is_jzhw'))
                 }),
                 )

    # 取消该商品缺货订单
    def pushPackageWeightAction(self, request, queryset):
        try:
            for package in queryset.filter(is_charged=False):
                tspw, state = TodaySmallPackageWeight.objects.get_or_create(package_id=package.out_sid)
                tspw.is_jzhw = package.isJZHW()
                tspw.save()
        except Exception, exc:
            messages.error(request, '出错信息:%s' % exc.message)

    pushPackageWeightAction.short_description = u"添加到今日小包上传列表"

    actions = ['pushPackageWeightAction', ]


admin.site.register(LogisticOrder, LogisticOrderAdmin)
