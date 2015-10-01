# -*- coding:utf-8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from django.http import HttpResponseRedirect

from shopback.base import log_action, ADDITION, CHANGE
from shopback.base.admin import MyAdmin
from .models import (
    SaleProduct,
    SaleSupplier,
    SaleCategory,
    SupplierCharge
)
from .filters import DateScheduleFilter, CategoryFilter, BuyerGroupFilter
from . import permissions as perms


class SaleSupplierAdmin(MyAdmin):
    list_display = ('id', 'supplier_code', 'supplier_name_link', 'platform',
                    'charge_link', 'category_select', 'progress', 'created', 'modified')
    list_display_links = ('id',)
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('progress', 'status', 'platform',
                   CategoryFilter,
                   )

    search_fields = ['supplier_name', 'supplier_code']

    def charge_link(self, obj):

        if obj.status == SaleSupplier.CHARGED:
            scharge = SupplierCharge.objects.get(supplier_id=obj.id, status=SupplierCharge.EFFECT)
            if obj.platform == "manualinput":
                return u'<a href="/supplychain/supplier/line_product/?status=selected&sale_supplier={0}" target="_blank">{1}</a>'.format(
                    obj.id,
                    u'[ %s ]' % scharge.employee.username)
            else:
                return u'<a href="/supplychain/supplier/product/?status=selected&sale_supplier={0}" target="_blank">{1}</a>'.format(
                    obj.id,
                    u'[ %s ]' % scharge.employee.username)

        if obj.status == SaleSupplier.FROZEN:
            return obj.get_status_display()

        return (
            '<a href="javascript:void(0);" class="btn btn-primary btn-charge" style="color:white;" sid="{0}">接管</a></p>'.format(
                obj.id))

    charge_link.allow_tags = True
    charge_link.short_description = u"接管信息/操作"

    def supplier_name_link(self, obj):
        return u'<a href="/admin/supplier/saleproduct/?sale_supplier={0}" target="_blank">{1}</a>'.format(
            obj.id, obj.supplier_name)

    supplier_name_link.allow_tags = True
    supplier_name_link.short_description = u"供应商"

    def category_list(self):
        if hasattr(self, "categorys"):
            return self.categorys
        self.categorys = SaleCategory.objects.all()
        return self.categorys


    def category_select(self, obj):

        categorys = self.category_list()

        cat_list = ["<select class='category_select' sid='%s'>" % obj.id]
        cat_list.append("<option value=''>-------------------</option>")
        for cat in categorys:
            if obj.category == cat:
                cat_list.append("<option value='%s' selected>%s</option>" % (cat.id, cat.name))
                continue
            cat_list.append("<option value='%s'>%s</option>" % (cat.id, cat.name))
        cat_list.append("</select>")

        return "".join(cat_list)

    category_select.allow_tags = True
    category_select.short_description = u"所属类目"

    # --------设置页面布局----------------
    fieldsets = ((u'客户基本信息:', {
        'classes': ('expand',),
        'fields': (('supplier_name', 'supplier_code')
                   , ('main_page', 'category', 'platform')
                   , ('contact', 'fax')
                   , ('phone', 'mobile')
                   , ('zip_code', 'email')
                   , ('address', 'progress', 'status')
                   , ('account_bank', 'account_no')
                   , ('memo',)
                   )}),)

    class Media:
        css = {
            "all": (
                "admin/css/forms.css", "css/admin/dialog.css", "css/admin/common.css", "jquery/jquery-ui-1.10.1.css")}
        js = ("js/admin/adminpopup.js", "js/supplier_change_list.js")

    def get_queryset(self, request):

        search_q = request.GET.get('q', '').strip()
        qs = super(SaleSupplierAdmin, self).get_queryset(request)
        if search_q:
            return qs

        if request.user.is_superuser:
            return qs
        scharges = SupplierCharge.objects.filter(employee=request.user, status=SupplierCharge.EFFECT)
        supplier_ids = [s.supplier_id for s in scharges]

        return qs.filter(
            models.Q(status=SaleSupplier.UNCHARGE) | models.Q(id__in=supplier_ids, status=SaleSupplier.CHARGED))

    def get_readonly_fields(self, request, obj=None):

        if 'status' not in self.readonly_fields:
            self.readonly_fields = self.readonly_fields + ('status',)
        return self.readonly_fields

    def batch_charge_action(self, request, queryset):
        """ 商家批量接管 """

        employee = request.user
        queryset = queryset.filter(status=SaleSupplier.UNCHARGE)

        for supplier in queryset:

            if SaleSupplier.objects.charge(supplier, employee):
                log_action(request.user.id, supplier, CHANGE, u'接管成功')

        self.message_user(request, u"======= 商家批量接管成功 =======")

        return HttpResponseRedirect("./")

    batch_charge_action.short_description = "批量接管".decode('utf8')

    def batch_uncharge_action(self, request, queryset):
        """ 商家批量取消接管 """

        employee = request.user
        queryset = queryset.filter(status=SaleSupplier.CHARGED)

        for supplier in queryset:

            if SaleSupplier.objects.uncharge(supplier, employee):
                log_action(request.user.id, supplier, CHANGE, u'取消接管')

        self.message_user(request, u"======= 商家批量取消接管成功 =======")

        return HttpResponseRedirect("./")

    batch_uncharge_action.short_description = "批量取消接管".decode('utf8')

    actions = ['batch_charge_action', 'batch_uncharge_action']


admin.site.register(SaleSupplier, SaleSupplierAdmin)


class SaleCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'parent_cid', 'full_name', 'is_parent', 'status', 'sort_order', 'created')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    def full_name(self, obj):
        return '%s' % obj

    full_name.allow_tags = True
    full_name.short_description = u"全称"

    ordering = ['parent_cid', '-sort_order', ]

    list_filter = ('status', 'is_parent')
    search_fields = ['id', 'parent_cid', 'name']


admin.site.register(SaleCategory, SaleCategoryAdmin)


class SaleProductAdmin(MyAdmin):
    category_list = []
    list_display = ('outer_id_link', 'pic_link', 'title_link', 'on_sale_price', 'std_sale_price', 'supplier_link',
                    'category_select', 'hot_value', 'sale_price', 'sale_time_select', 'select_Contactor', 'modified', 'status')
    # list_display_links = ('outer_id',)
    # list_editable = ('update_time','task_type' ,'is_success','status')

#     ordering = ('-hot_value',)
    date_hierarchy = 'sale_time'
    list_filter = ('status', ('sale_time', DateScheduleFilter),
                   CategoryFilter, 'platform', BuyerGroupFilter)
    search_fields = ['=id', 'title', '=outer_id', '=sale_supplier__supplier_name', '=contactor__username']
    list_per_page = 40

    # --------设置页面布局----------------
    fieldsets = ((u'客户基本信息:', {
        'classes': ('expand',),
        'fields': (('outer_id', 'title')
                   , ('pic_url', 'product_link')
                   , ('price', 'sale_price')
                   , ('on_sale_price', 'std_sale_price')
                   , ('sale_supplier', 'sale_category')
                   , ('platform', 'hot_value', 'status')
                   , ('sale_time', 'reserve_time', 'contactor')
                   , ('memo',)
                   )}),)

    #
    def outer_id_link(self, obj):

        test_link = u'<div style="width:120px;font-size:12px;"><a href="/admin/supplier/saleproduct/{0}/" onclick="return showTradePopup(this);">{1}</a>'.format(
            obj.id, obj.outer_id or '')

        if obj.status in (SaleProduct.SELECTED, SaleProduct.PASSED, SaleProduct.PURCHASE,
                          SaleProduct.SCHEDULE) and obj.outer_id:
            # test_link += u'<br><br><a href="/supplychain/supply/sample/add_sample/?outer_id={0}&title={1}&pic_url={2}&sale_supplier={3}&sale_price={4}&std_sale_price={5}" class="btn" target="_blank" >{6}</a>'
            #
            # test_link = test_link.format(obj.outer_id, obj.title, obj.pic_url, obj.sale_supplier, obj.sale_price,
            #                              obj.std_sale_price,
            #                              u'加入样品库')
            test_link += u'<br><br><a href="/static/add_item.html?supplier_id={0}&saleproduct={1}" class="btn" target="_blank" >{2}</a>' \
                         u'<a href="/supplychain/supplier/bdproduct/{1}/" class="btn" target="_blank" >{3}</a>'
            test_link = test_link.format(obj.sale_supplier.id, obj.id, u'加入库存商品', u'关联库存商品')
        test_link += u'</div>'

        return test_link

    outer_id_link.allow_tags = True
    outer_id_link.short_description = u"外部ID"

    def category_select(self, obj):

        categorys = self.category_list

        cat_list = ["<select class='sale_category_select' spid='%s'>" % obj.id]
        cat_list.append("<option value=''>-------------------</option>")
        for cat in categorys:

            if obj and obj.sale_category == cat:
                cat_list.append("<option value='%s' selected>%s</option>" % (cat.id, cat))
                continue

            cat_list.append("<option value='%s'>%s</option>" % (cat.id, cat))
        cat_list.append("</select>")

        return "".join(cat_list)

    category_select.allow_tags = True
    category_select.short_description = u"所属类目"


    def get_readonly_fields(self, request, obj=None):

        rset = set([])
        if self.readonly_fields:
            rset = set(self.readonly_fields)

        rset.add('sale_supplier')
        contactor_name = 'contactor'
        rset.add(contactor_name)
#         if not perms.has_sale_product_mgr_permission(request.user):
#             rset.add(contactor_name)
# 
#         if perms.has_sale_product_mgr_permission(request.user):
#             if contactor_name in rset:
#                 rset.remove(contactor_name)

        return rset

    def pic_link(self, obj):
        #         abs_pic_url = '%s%s'%(settings.MEDIA_URL,obj.pic_url)
        return (u'<a href="%s" target="_blank"><img src="%s" width="120px" height="100px" title="%s"/></a>' % (
            obj.product_link, obj.pic_url, obj.get_platform_display()))

    pic_link.allow_tags = True
    pic_link.short_description = u"商品图片"

    def title_link(self, obj):
        #         abs_pic_url = '%s%s'%(settings.MEDIA_URL,obj.pic_url)
        ignore_style = ''
        ignore_val = ''
        ignore_status = ''
        if obj.status == SaleProduct.WAIT:
            ignore_style = 'btn-info btn-ignore'
            ignore_val = u'忽略'
            ignore_status = SaleProduct.IGNORED
        elif obj.status in (SaleProduct.IGNORED, SaleProduct.REJECTED):
            ignore_val = u'已忽略'
        elif obj.status == SaleProduct.SCHEDULE:
            ignore_val = ''
        else:
            ignore_style = 'btn-info btn-ignore'
            ignore_val = u'淘汰'
            ignore_status = SaleProduct.REJECTED

        select_style = ''
        select_val = ''
        if obj.status == SaleProduct.WAIT:
            select_style = 'btn-success btn-selected'
            select_val = u'入围'
        elif obj.status in (SaleProduct.SELECTED, SaleProduct.PURCHASE, SaleProduct.PASSED, SaleProduct.SCHEDULE):
            select_val = u'已入围'
        else:
            select_val = u'已淘汰'

        return (u'<div style="width:350px;">'
                + u'<a href="javascript:void(0);" class="btn {0}" pid="{1}" status="{7}">{2}</a>'
                + u'<div  class="well well-content">{3}</div>'
                + u'<a href="javascript:void(0);" class="btn {4}" pid="{5}" >{6}</a></div>').format(ignore_style,
                                                                                                    obj.id,
                                                                                                    ignore_val,
                                                                                                    obj.title,
                                                                                                    select_style,
                                                                                                    obj.id,
                                                                                                    select_val,
                                                                                                    ignore_status)

    title_link.allow_tags = True
    title_link.short_description = u"标题"

    def supplier_link(self, obj):
        base_link = u'<div  style="width:150px;font-size:20px;"><label>{0}</lable>'.format(
            obj.sale_supplier and obj.sale_supplier.supplier_name or '')
        if obj.status in (SaleProduct.SELECTED, SaleProduct.PURCHASE, SaleProduct.WAIT, SaleProduct.PASSED,
                          SaleProduct.SCHEDULE) and obj.sale_supplier:
            if obj.platform == u'manualinput':
                base_link += u'<br><br><a href="/supplychain/supplier/line_product/?status={0}&sale_supplier={1}"  target="_blank" >{2}</a></div>'
                base_link = base_link.format(obj.status,
                                             obj.sale_supplier.id,
                                             u'洽谈')
            else:
                base_link += u'<br><br><a href="/supplychain/supplier/product/?status={0}&sale_supplier={1}"  target="_blank" >{2}</a></div>'
                base_link = base_link.format(obj.status,
                                             obj.sale_supplier.id,
                                             u'洽谈')
        return base_link

    supplier_link.allow_tags = True
    supplier_link.short_description = u"供应商"

    # 选择上架时间
    def sale_time_select(self, obj):
        # 只有通过　和排期状态的才可以修改该时间
        if obj.status == SaleProduct.PASSED or obj.status == SaleProduct.SCHEDULE:
            if obj.sale_time is None:
                s ='<input type="text" id="{0}" readonly="true" class="select_saletime form-control datepicker" name="" value=""/>'.format(obj.id)
            else:
                sale_time = obj.sale_time.strftime("%y-%m-%d")
                s ='<input type="text" id="{0}" readonly="true" class="select_saletime form-control datepicker" name={1} value="{1}"/>'.format(obj.id, sale_time)
        else:
            s = "非通过或排期状态"
        return s
    sale_time_select.allow_tags = True
    sale_time_select.short_description = u"上架时间"

    class Media:
        css = {
            "all": (
                "admin/css/forms.css", "css/admin/dialog.css", "css/admin/common.css", "jquery/jquery-ui-1.10.1.css",
             "jquery-timepicker-addon/timepicker/jquery-ui-timepicker-addon.css")}
        js = ("jquery/jquery-1.8.13.min.js", "js/admin/adminpopup.js", "js/supplier_change_list.js",
              "js/select_buyer_group.js","jquery/jquery-ui-1.8.13.min.js","jquery-timepicker-addon/timepicker/jquery-ui-timepicker-addon.js",
              "jquery-timepicker-addon/js/jquery-ui-timepicker-zh-CN.js")

    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        self.category_list = SaleCategory.objects.all()

        return super(SaleProductAdmin, self).get_changelist(request, **kwargs)

    def response_add(self, request, obj, post_url_continue='../%s/'):

        if not obj.contactor:
            obj.contactor = request.user
            obj.save()

        return super(SaleProductAdmin, self).response_add(request, obj, post_url_continue=post_url_continue)

    def select_Contactor(self, obj):
        from models_buyer_group import BuyerGroup

        buyer_groups = (0, 1, 2, 3)
        name = str(obj.contactor)
        BuyerGroupNo = (u'未分组', u'A组', u'B组', u'C组')
        target_user_group = BuyerGroup.objects.filter(buyer_name=name)
        html = [
            "<p id='item_id_{1}'>{0}</p><select id='select_buyer_group_{1}' name='selse' onchange='select_buyter({1})'>".format(
                obj.contactor, obj.id)]
        for group in buyer_groups:
            if target_user_group.count() > 0 and target_user_group[0].buyer_group == group:
                html.append("<option selected='selected' value='{0}'>{1}</option>".format(group, BuyerGroupNo[group]))
            else:
                html.append("<option value='{0}'>{1}</option>".format(group, BuyerGroupNo[group]))

        html.append("</select>")
        return "".join(html)

    select_Contactor.allow_tags = True
    select_Contactor.short_description = u"接洽人"


admin.site.register(SaleProduct, SaleProductAdmin)

from models_buyer_group import BuyerGroup


class BuyerGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer_name', 'buyer_group', 'created')
    list_display_links = ('id', 'buyer_name')
    list_filter = ('id', 'buyer_group', 'created')
    search_fields = ['=id', '=buyer_name']


admin.site.register(BuyerGroup, BuyerGroupAdmin)