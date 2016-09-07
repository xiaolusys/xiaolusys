# -*- coding:utf-8 -*-
import re
import json
import hashlib
import datetime
from cStringIO import StringIO

from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from django.http import HttpResponseRedirect

from core.admin import ApproxAdmin
from core.options import log_action, ADDITION, CHANGE
from core.upload import upload_public_to_remote, generate_public_url
from .models import (
    SaleProduct,
    SaleSupplier,
    SaleCategory,
    SaleCategoryVersion,
    SupplierCharge,
    SupplierFigure,
    HotProduct,
    SupplierZone,
    BuyerGroup,
    SalePraise,
    CategoryPreference,
    PreferencePool
)

from .forms import SaleSupplierForm
from .filters import DateScheduleFilter, CategoryFilter, BuyerGroupFilter, SupplierZoneFilter
from core.filters import DateFieldListFilter
from . import permissions as perms
from django.contrib.admin.views.main import ChangeList
from supplychain.supplier.models import SaleProduct, SaleProductManage, SaleProductManageDetail

from shopback.items.models import Product
from django.contrib.auth.models import User

import logging
logger = logging.getLogger(__name__)

class SaleSupplierChangeList(ChangeList):

    def get_queryset(self,request):
        qs = self.root_queryset

        search_q = request.GET.get('q', '').strip()
        if re.compile('^[\w]+[\.][\w]+$').match(search_q):
            (self.filter_specs, self.has_filters, remaining_lookup_params,
             use_distinct) = self.get_filters(request)

            for filter_spec in self.filter_specs:
                new_qs = filter_spec.queryset(request, qs)
                if new_qs is not None:
                    qs = new_qs

            ordering = self.get_ordering(request, qs)
            qs = qs.order_by(*ordering)
            scharge = SupplierCharge.objects.filter(employee__username=search_q, status=SupplierCharge.EFFECT)
            sc = set([s.supplier_id for s in scharge])
            suppliers = qs.filter(id__in=sc)
            return suppliers
        return super(SaleSupplierChangeList, self).get_queryset(request)


class SaleSupplierAdmin(ApproxAdmin):
    list_display = ('id', 'supplier_code', 'supplier_name_link', 'charge_link',
                    'total_select_num', 'total_sale_amount', 'total_refund_amount', 'avg_post_days',
                    'category_select', 'progress', 'last_select_time', 'last_schedule_time',
                    'supplier_type_choice', 'supplier_zone_choice', 'address', 'ware_by', 'return_ware_by', 'memo_well')
    list_display_links = ('id',)
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('level', 'progress', 'status', 'platform', CategoryFilter, 'supplier_type', SupplierZoneFilter)
    search_fields = ['supplier_name', 'supplier_code', '=id']
    form = SaleSupplierForm
    list_per_page = 15

    def last_select_time_display(self, obj):
        return obj.last_select_time.date()
    #
    # last_select_time_display.allow_tags = True
    # last_select_time_display.short_description = u"最后选款日期"

    def last_schedule_time_display(self, obj):
        return obj.last_schedule_time.date()

    # last_schedule_time_display.allow_tags = True
    # last_schedule_time_display.short_description = u"最后上架日期"

    def supplier_zone_choice(self, obj):
        select_list = ['<select id="supplier_zone_{0}" class="supplier_zone" cid="{0}">'.format(obj.id)]
        supplier_zones = SupplierZone.objects.all()
        for zone in supplier_zones:
            if obj.supplier_zone == zone.id:
                select_list.append('<option value="{0}" selected="selected">{1}</option>'.format(zone.id, zone.name))
                continue
            select_list.append('<option value="{0}">{1}</option>'.format(zone.id, zone.name))
        select_list.append('</select>')
        return "".join(select_list)

    supplier_zone_choice.allow_tags = True
    supplier_zone_choice.short_description = u"供应商片区"

    def supplier_type_choice(self, obj):
        select_list = ['<select id="supplier_type_{0}" class="supplier_type" cid="{0}">'.format(obj.id)]
        for k, v in SaleSupplier.SUPPLIER_TYPE:
            if obj.supplier_type == k:
                select_list.append('<option value="{0}" selected="selected">{1}</option>'.format(k, v))
                continue
            select_list.append('<option value="{0}">{1}</option>'.format(k, v))
        return "".join(select_list)
    supplier_type_choice.allow_tags = True
    supplier_type_choice.short_description = u"类型"

    def charge_link(self, obj):
        if obj.status == SaleSupplier.CHARGED:  # 如果是已经接管
            scharge = SupplierCharge.objects.get(supplier_id=obj.id, status=SupplierCharge.EFFECT)
            return u'<a href="/supplychain/supplier/product/?status=purchase&sale_supplier={0}"' \
                   u' target="_blank">{1}</a>'.format(obj.id, u'[ %s ]' % scharge.employee.username)

        if obj.status == SaleSupplier.FROZEN:   # 如果是冻结状态　则显示冻结
            return obj.get_status_display()
        # 默认显示　接管按钮
        return ('<a href="javascript:void(0);" class="btn btn-primary btn-charge"'
                ' style="color:white;" sid="{0}">接管</a></p>'.format(obj.id))

    charge_link.allow_tags = True
    charge_link.short_description = u"接管/操作"

    def supplier_name_link(self, obj):
        span_style="font-size:16px;"
        if obj.level == SaleSupplier.LEVEL_GOOD:
            span_style += "background-color:green;color:white;"
        elif obj.level == SaleSupplier.LEVEL_INFERIOR:
            span_style += "color:gray;font-size:10px;"
        if not obj.is_active():
            span_style += 'text-decoration:line-through;'
        return u'<a href="/admin/supplier/saleproduct/?sale_supplier={0}" target="_blank">' \
               u'<span style="{3}" class="supplier_name">{1}&nbsp;({2})</span>' \
               u'</a>'.format(
            obj.id, obj.supplier_name, obj.get_level_display(),span_style)

    supplier_name_link.allow_tags = True
    supplier_name_link.short_description = u"供应商"

    def category_list(self):
        if hasattr(self, "categorys"):
            return self.categorys
        self.categorys = SaleCategory.get_normal_categorys()
        return self.categorys

    def get_changelist(self, request, **kwargs):
        return SaleSupplierChangeList

    def category_select(self, obj):
        categorys = self.category_list()
        cat_list = ["<select class='category_select' sid='%s'>" % obj.id]
        cat_list.append("<option value='%s'>%s</option>"%(obj.category and obj.category.id or '', obj.category or '-----------'))
        for cat in categorys:
            if obj.category == cat:
                cat_list.append("<option value='%s' selected>%s</option>" % (cat.id, cat))
                continue
            cat_list.append("<option value='%s'>%s</option>" % (cat.id, cat))
        cat_list.append("</select>")

        return "".join(cat_list)

    category_select.allow_tags = True
    category_select.short_description = u"所属类目"

    def memo_well(self, obj):
        return u'<div style="width:200px;"><div class="well well-content">[特长]：{0}</div><br><div class="well well-content">[备注]：{1}</div></div>'.format(
            obj.speciality, obj.memo)

    memo_well.allow_tags = True
    memo_well.short_description = u"特长及备注"

    # --------设置页面布局----------------\
    fieldsets = ((u'供应商基本信息:', {
                    'classes': ('expand',),
                    'fields': (('supplier_name', 'product_link', 'supplier_code')
                               , ('main_page', 'category', 'platform')
                               , ('contact', 'fax')
                               , ('phone', 'mobile')
                               , ('email', 'zip_code')
                               , ('address', 'progress', 'status')
                               , ('account_bank', 'account_no')
                               , ('supplier_type', 'supplier_zone', 'ware_by', 'return_ware_by')
                               , ('memo','delta_arrive_days')
                               )
                 }),
                 (u'供应商数据:', {
                    'classes': ('expand',),
                    'fields': (('level', 'last_select_time', 'last_schedule_time')
                               , ('total_select_num', 'total_sale_num', 'total_sale_amount')
                               , ('total_refund_num', 'total_refund_amount', 'avg_post_days')
                               , ('return_goods_limit_days', 'speciality')
                               )
                 }))

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':64, 'maxlength': '256',})},
        models.FloatField: {'widget': TextInput(attrs={'size':24})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }

    class Media:
        css = {
            "all": (
                "admin/css/forms.css", "css/admin/dialog.css", "css/admin/common.css", "jquery/jquery-ui-1.10.1.css",
                "css/supplier_changelist.css")}
        js = ("js/admin/adminpopup.js", "js/supplier_change_list.js")

    """
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
    """

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

    batch_charge_action.short_description = u"批量接管"

    def batch_uncharge_action(self, request, queryset):
        """ 商家批量取消接管 """

        employee = request.user
        queryset = queryset.filter(status=SaleSupplier.CHARGED)

        for supplier in queryset:

            if SaleSupplier.objects.uncharge(supplier, employee):
                log_action(request.user.id, supplier, CHANGE, u'取消接管')

        self.message_user(request, u"======= 商家批量取消接管成功 =======")

        return HttpResponseRedirect("./")

    batch_uncharge_action.short_description = u"批量取消接管"


    def batch_taotai_action(self, request, queryset):
        """ 批量淘汰 """
        supplier_ids = []
        for supplier in queryset:
            supplier_ids.append(supplier.id)
        saleproduct_ids = []
        for saleproduct in SaleProduct.objects.filter(sale_supplier_id__in=supplier_ids).exclude(status=SaleProduct.REJECTED):
            saleproduct_ids.append(saleproduct.id)

        today = datetime.datetime.now().date()
        product_ids = []
        for product in Product.objects.filter(sale_product__in=saleproduct_ids, status=Product.NORMAL, sale_time__gte=today):
            product_ids.append(product.id)
        if product_ids:
            self.message_user(request, '以下商品正在上架')
            return HttpResponseRedirect('/admin/items/product/?id__in=%s' % ','.join([str(x) for x in product_ids]))

        employee = request.user
        for saleproduct in SaleProduct.objects.filter(id__in=saleproduct_ids):
            saleproduct.status = SaleProduct.REJECTED
            saleproduct.save()
            log_action(employee.id, saleproduct, CHANGE, u'淘汰成功')

        for supplier in queryset:
            supplier.progress = SaleSupplier.REJECTED
            supplier.save()
            log_action(employee.id, supplier, CHANGE, u'淘汰成功')
        self.message_user(request, u"======= 商家批量淘汰成功 =======")
        return HttpResponseRedirect("./")

    batch_taotai_action.short_description = u"批量淘汰"
    actions = ['batch_charge_action', 'batch_uncharge_action', 'batch_taotai_action']


admin.site.register(SaleSupplier, SaleSupplierAdmin)


class SaleCategoryAdmin(admin.ModelAdmin):
    list_display = ('cid', 'parent_cid', 'category_pic_display', 'full_name', 'grade', 'is_parent', 'status', 'sort_order', 'created')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    def full_name(self, obj):
        return '%s' % obj

    full_name.allow_tags = True
    full_name.short_description = u"全称"

    ordering = ['parent_cid', '-sort_order', ]

    list_filter = ('status', 'is_parent')
    search_fields = ['=id', '=parent_cid', '=name']

    def category_pic_display(self, obj):
        return '<img src="%s" style="width:40px;height:40px;">'%obj.cat_pic

    category_pic_display.allow_tags = True
    category_pic_display.short_description = u"类目图片"


admin.site.register(SaleCategory, SaleCategoryAdmin)


class SaleCategoryVersionAdmin(ApproxAdmin):
    list_display = ('id', 'version', 'sha1', 'memo', 'status')
    search_fields = ['=id', '=version', '=sha1']

    list_filter = ('status',)

    def response_change(self, request, obj, *args, **kwargs):
        # 订单处理页面
        opts = obj._meta
        # Handle proxy models automatically created by .only() or .defer()
        verbose_name = opts.verbose_name
        if obj._deferred:
            opts_ = opts.proxy_for_model._meta
            verbose_name = opts_.verbose_name
        pk_value = obj._get_pk_val()
        obj.status = False
        if not obj.download_url:
            try:
                category_data = SaleCategory.get_salecategory_jsontree()
                districts_jsonstring = json.dumps(category_data, indent=2)
                string_io = StringIO(districts_jsonstring)
                resp = upload_public_to_remote(obj.gen_filepath(), string_io)
                obj.sha1 = hashlib.sha1(districts_jsonstring).hexdigest()
                logger.info('upload salecategory resp:%s' % resp)
                if resp.status_code != 200:
                    obj.memo += u'分类数据文件上传异常:%s' % resp.text_body
                    obj.save(update_fields=['memo', 'sha1'])
                    raise Exception(u'分类数据文件上传异常:%s' % resp.text_body)

                obj.download_url = generate_public_url(obj.gen_filepath())
                obj.status = True
                obj.save(update_fields=['download_url', 'memo', 'sha1', 'status'])
            except Exception, exc:
                self.message_user(request, u"类目版本更新失败：%s" % (exc.message))
                logger.error(u"类目版本更新失败：%s" % (exc.message), exc_info=True)

        return super(SaleCategoryVersionAdmin, self).response_change(request, obj, *args, **kwargs)


admin.site.register(SaleCategoryVersion, SaleCategoryVersionAdmin)


class SupplierZoneAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ['id', 'name']

admin.site.register(SupplierZone, SupplierZoneAdmin)


class SaleProductAdmin(ApproxAdmin):
    category_list = []
    list_display = ('outer_id_link', 'pic_link', 'title_link', "memo_display", 'librarian_select',
                    'select_Contactor', 'supplier_link', 'category_select',
                    'sale_price', 'on_sale_price', 'sale_time_select',  'status_link')
    # list_display_links = ('outer_id',)
    # list_editable = ('update_time','task_type' ,'is_success','status')

    # ordering = ('-hot_value',)
    list_filter = ('status', ('sale_time', DateScheduleFilter),CategoryFilter,'is_changed',
                   ('modified', DateFieldListFilter), 'platform', BuyerGroupFilter,
                   ('created', DateFieldListFilter), 'librarian', "buyer")
    search_fields = ['=id', 'title', '=outer_id', '=sale_supplier__supplier_name', '=contactor__username']
    list_per_page = 25

    # --------设置页面布局----------------
    fieldsets = ((u'客户基本信息:', {
        'classes': ('expand',),
        'fields': (('outer_id', 'title')
                   , ('pic_url', 'product_link')
                   , ('price', 'sale_price')
                   , ('on_sale_price', 'std_sale_price')
                   , ('supplier_sku', 'remain_num')
                   , ('sale_supplier', 'sale_category')
                   , ('platform', 'hot_value','status','is_changed')
                   , ('sale_time', 'reserve_time', 'contactor')
                   , ('memo',), ('voting','orderlist_show_memo')
                   )}),)

    # def sale_info(self, obj):
    #     """上架销售信息"""
    #     if obj.status != SaleProduct.SCHEDULE:
    #         return ''
    #     product_outer_ids = obj.item_products.values("outer_id")
    #     from statistics.models import SaleStats
    #     # 日报　产品　统计
    #     status_map = {0: u"未付款",
    #                   1: u"已付款",
    #                   2: u"发货前退款",
    #                   3: u"缺货退款",
    #                   4: u"退货退款"}
    #     data = {}
    #     stats = SaleStats.objects.filter(timely_type=6,
    #                                      record_type=4,
    #                                      current_id__in=product_outer_ids).values("date_field", "status", 'num')
    #     for st in stats:
    #         if st['date_field'] not in data:
    #             data[st['date_field']] = {u'未付款': 0,
    #                                       u'已付款': 0,
    #                                       u'发货前退款': 0,
    #                                       u'缺货退款': 0,
    #                                       u'退货退款': 0}
    #             data[st['date_field']][status_map[st['status']]] = st['num']
    #         else:
    #             data[st['date_field']][status_map[st['status']]] += st['num']
    #     html = []
    #     for k1, v1 in data.iteritems():
    #         html.append('<p>%s<br>' % k1.strftime("%Y-%m-%d"))
    #         for status, num in v1.iteritems():
    #             html.append('<span>%s</span>: <em>%s</em><br>' % (status, num))
    #         html.append('</p>')
    #     return ''.join(html)
    # sale_info.allow_tags = True
    # sale_info.short_description = u"销售信息"

    def outer_id_link(self, obj):
        test_link = u'<div style="width:120px;font-size:12px;"><a href="/admin/supplier/saleproduct/{0}/" onclick="return showTradePopup(this);">{1}</a>'.format(
            obj.id, obj.outer_id or '')

        if obj.status in (SaleProduct.SELECTED, SaleProduct.PASSED, SaleProduct.PURCHASE,
                          SaleProduct.SCHEDULE) and obj.outer_id and obj.sale_supplier:
            # test_link += u'<br><br><a href="/supplychain/supply/sample/add_sample/?outer_id={0}&title={1}&pic_url={2}&sale_supplier={3}&sale_price={4}&std_sale_price={5}" class="btn" target="_blank" >{6}</a>'
            #
            # test_link = test_link.format(obj.outer_id, obj.title, obj.pic_url, obj.sale_supplier, obj.sale_price,
            #                              obj.std_sale_price,
            #                              u'加入样品库')
            test_link += u'<br><br><a href="/apis/items/v1/product?supplier_id={0}&saleproduct={1}" class="btn" target="_blank" >{2}</a>' \
                         u'<a href="/supplychain/supplier/bdproduct/{1}/" class="btn" target="_blank" >{3}</a>'
            history_sale = u'加入库存商品'
            if Product.objects.filter(sale_product=obj.id).exists():
                history_sale = u'<span style="color:red">加入库存商品</span>'
            test_link = test_link.format(obj.sale_supplier.id, obj.id, history_sale, u'关联库存商品')
        test_link += u'</div>'

        return test_link

    outer_id_link.allow_tags = True
    outer_id_link.short_description = u"外部ID"

    def librarian_select(self, obj):
        select_librarian = ['资料员：<br><select class="sale_librarian_select" spid="%s" onchange="sale_librarian_select(this)">' % obj.id]
        select_librarian.append('<option value="">------</option>')
        librarian_users = User.objects.filter(is_staff=True, groups__name__in=(u'小鹿买手资料员', ))
        for user in librarian_users:
            if obj and obj.librarian == user.get_full_name():
                select_librarian.append('<option value="{0}" selected>{0}</option>'.format(user.get_full_name()))
                continue
            select_librarian.append('<option value="{0}">{0}</option>'.format(user.get_full_name()))
        select_librarian.append("</select><br><br>")
        librarian_select = "".join(select_librarian)

        select_buyer = ['采购员：<br><select class="sale_buyer_select" spid="%s" onchange="sale_buyer_select(this)">' % obj.id]
        select_buyer.append('<option value="">------</option>')
        buyer_users = User.objects.filter(is_staff=True, groups__name__in=(u'小鹿采购管理员', u'小鹿采购员'))
        for user in buyer_users:
            if obj and obj.buyer == user.get_full_name():
                select_buyer.append('<option value="{0}" selected>{0}</option>'.format(user.get_full_name()))
                continue
            select_buyer.append('<option value="{0}">{0}</option>'.format(user.get_full_name()))
        select_buyer.append("</select><br>")
        buyer_select = "".join(select_buyer)
        return librarian_select + buyer_select

    librarian_select.allow_tags = True
    librarian_select.short_description = u"人员分配"

    def category_select(self, obj):

        categorys = self.category_list
        cat_list = ["<select class='sale_category_select' spid='%s'>" % obj.id]
        cat_list.append("<option value='%s'>%s</option>"%(obj.sale_category and obj.sale_category.id or '',
                                                          obj.sale_category or '-----------'))
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
        if not perms.has_sale_product_mgr_permission(request.user):
            rset.add('is_changed')
#         if perms.has_sale_product_mgr_permission(request.user):
#             if contactor_name in rset:
#                 rset.remove(contactor_name)
        return rset

    def pic_link(self, obj):
        #         abs_pic_url = '%s%s'%(settings.MEDIA_URL,obj.pic_url)
        return (u'<div class="well well-content"><a href="%s" target="_blank"><img src="%s" width="120px" height="100px" '
                u'title="%s?imageMogr2/thumbnail/150/format/jpg/quality/90"/></a>'
                u'<br>%s<br></div>' % (
                    obj.product_link, obj.pic_url, obj.get_platform_display(), obj.created.strftime('%Y/%m/%d %H:%M')))

    pic_link.allow_tags = True
    pic_link.short_description = u"商品图片"

    def title_link(self, obj):
        try:
            HotProduct.objects.get(proid=obj.id)
            html = u'<br><br><a class="btn" target="_blank" href="/admin/supplier/hotproduct/?proid={0}">查看爆款</a>'.format(obj.id)
        except HotProduct.DoesNotExist:
            if obj.status == SaleProduct.WAIT:
                html = u'<br><br><a class="btn" target="_blank" cid="{0}" onclick="toMakeHot(this)">生成爆款</a>'.format(obj.id)
            else:
                html = u''
        except HotProduct.MultipleObjectsReturned:
            html = u'<br><br><a class="btn" target="_blank" href="/admin/supplier/hotproduct/?proid={0}">查看爆款</a>'.format(obj.id)
        return (u'<div style="width:100px;"><div class="well well-content">{0}</div></div>{1}').format(obj.title,html)

    title_link.allow_tags = True
    title_link.short_description = u"标题"

    def supplier_link(self, obj):
        base_link = u'<div style="width:90px;font-size:20px;"><a href="/admin/supplier/saleproduct/?sale_supplier={0}"><label>{1} &gt;&gt;</label></a>'.format(
            obj.sale_supplier and obj.sale_supplier.id or '',obj.sale_supplier and obj.sale_supplier.supplier_name or '')
        if obj.status in (SaleProduct.SELECTED, SaleProduct.PURCHASE, SaleProduct.WAIT, SaleProduct.PASSED,
                          SaleProduct.SCHEDULE) and obj.sale_supplier:
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
        tpl1 = """
        <input type="text" id="{0}" style="width:70px" readonly="true" class="select_saletime form-control datepicker" name="" value=""/>
        <p class="schedule_date" id="{0}"></p>
        <p class="sale_date" id="{0}"></p>
        """

        tpl2 = """
        <input type="text" id="{0}" style="width:70px" readonly="true" class="select_saletime form-control datepicker" name={1} value="{1}"/>
        <p class="schedule_date" id="{0}"></p>
        <p class="sale_date" id="{0}"></p>
        """

        if obj.status in (SaleProduct.PURCHASE,SaleProduct.PASSED,SaleProduct.SCHEDULE):
            if obj.sale_time is None:
                s =tpl1.format(obj.id)
            else:
                sale_time = obj.sale_time.strftime("%y-%m-%d")
                s =tpl2.format(obj.id, sale_time)
        else:
            s = "非可排期状态"
        return s
    sale_time_select.allow_tags = True
    sale_time_select.short_description = u"上架时间"

    def get_select_list(self,obj):
        slist = []
        if obj.status == SaleProduct.WAIT:
            slist.extend([SaleProduct.WAIT,
                          SaleProduct.SELECTED,
                          SaleProduct.PURCHASE,
                          SaleProduct.IGNORED])
        elif obj.status in (SaleProduct.SELECTED,
                            SaleProduct.PURCHASE):
            slist.extend([SaleProduct.SELECTED,
                          SaleProduct.PURCHASE,
                          SaleProduct.PASSED,
                          SaleProduct.REJECTED])
        elif obj.status == SaleProduct.PASSED:
            slist.extend([SaleProduct.PURCHASE,
                          SaleProduct.PASSED,
                          SaleProduct.SCHEDULE,
                          SaleProduct.REJECTED])
        elif obj.status == SaleProduct.SCHEDULE:
            slist.extend([SaleProduct.PURCHASE,
                          SaleProduct.PASSED,
                          SaleProduct.SCHEDULE,
                          SaleProduct.REJECTED])
        else:
            slist.append(obj.status)
        return slist

    def status_link(self, obj):
        s = []
        sel_list = self.get_select_list(obj)
        SDM = dict(SaleProduct.STATUS_CHOICES)
        s.append(u'<select class="status_select" pid={0}>')
        for sel in sel_list:
            selected = ''
            if sel == obj.status:
                selected = 'selected'
            s.append(u'<option value="%s" %s>%s</option>'%(sel,selected,SDM.get(sel)))
        s.append(u'</select>')
        return ''.join(s).format(obj.id)

    status_link.allow_tags = True
    status_link.short_description = u"状态／操作"

    def select_Contactor(self, obj):

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

    def memo_display(self, obj):
        res = ''
        if obj.memo != u'':
            res = u'<div style="width:100px;"><div class="well well-content">{0}</div></div>'.format(obj.memo)
        return res
    memo_display.allow_tags = True
    memo_display.short_description = u"备注"

    class Media:
        css = {
            "all": (
                "admin/css/forms.css", "css/admin/dialog.css", "css/admin/common.css", "css/common.css", "jquery/jquery-ui-1.10.1.css",
             "jquery-timepicker-addon/timepicker/jquery-ui-timepicker-addon.css")}
        js = ("jquery/jquery-1.8.13.min.js", "js/admin/adminpopup.js", "js/supplier_change_list.js",
              "js/select_buyer_group.js","jquery/jquery-ui-1.8.13.min.js","jquery-timepicker-addon/timepicker/jquery-ui-timepicker-addon.js",
              "jquery-timepicker-addon/js/jquery-ui-timepicker-zh-CN.js","js/make_hot.js")+ \
              ('//cdn.bootcss.com/plupload/2.1.7/plupload.full.min.js','script/qiniu.js',"js/image_productreview.js")

    def get_actions(self, request):
        user = request.user
        actions = super(SaleProductAdmin, self).get_actions(request)

        if user.is_superuser:
            return actions
        valid_actions = set([])
        if user.has_perm('supplier.schedule_manage'):  # 排期管理
            valid_actions.add('schedule_manage_action')
        if user.has_perm('supplier.sale_product_mgr'):
            valid_actions.add('voting_action')
            valid_actions.add('cancel_voting_action')
        valid_actions.add('rejected_action')
        unauth_actions = []
        for action in actions.viewkeys():
            action_ss = str(action)
            if action_ss not in valid_actions:
                unauth_actions.append(action_ss)

        for action in unauth_actions:
            del actions[action]
        return actions
    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        self.category_list = SaleCategory.get_normal_categorys().filter(is_parent=False).order_by('parent_cid')

        return super(SaleProductAdmin, self).get_changelist(request, **kwargs)

    def delete_model(self, request, obj):
        """
        Given a model instance delete it from the database.
        """
        if obj.status == SaleProduct.WAIT:
            obj.status = SaleProduct.IGNORED
        else:
            obj.status = SaleProduct.REJECTED
        obj.save()

    def response_add(self, request, obj, post_url_continue='../%s/'):

        if not obj.contactor:
            obj.contactor = request.user
            obj.save()

        return super(SaleProductAdmin, self).response_add(request, obj, post_url_continue=post_url_continue)

    def voting_action(self, request, queryset):
        """  设置选品投票  取样通过　的产品可以设置参与投票　"""
        no_votigs = queryset.filter(voting=False, status__in=(SaleProduct.PURCHASE, SaleProduct.PASSED))
        no_votigs.update(voting=True)
        mes = u"设置选品参与投票完成"
        self.message_user(request, mes)

    voting_action.short_description = u"设置选品投票"

    def cancel_voting_action(self, request, queryset):
        """  取消选品投票  """
        votigs = queryset.filter(voting=True)
        votigs.update(voting=False)
        mes = u"取消选品投票设置完成"
        self.message_user(request, mes)

    cancel_voting_action.short_description = u"取消选品投票"

    def rejected_action(self,request,queryset):
        """ 批量淘汰选品 """
        sproducts = queryset.exclude(status__in=(SaleProduct.REJECTED,SaleProduct.IGNORED))
        for sproduct in sproducts:
            sproduct.status = SaleProduct.REJECTED
            sproduct.save()
            log_action(request.user.id,sproduct,CHANGE,u'淘汰选品')
        mes = u"已淘汰%s个选品"%sproducts.count()
        self.message_user(request, mes)

    rejected_action.short_description = u"淘汰选品"

    def schedule_manage_action(self, request, queryset):
        """  排期管理  """
        try:
            sale_time = queryset[0].sale_time.date()
        except:
            self.message_user(request, u"有时间不对")
            return
        product_num = 0
        mgr_p, state = SaleProductManage.objects.get_or_create(sale_time=sale_time)
        if not state and mgr_p.lock_status:
            self.message_user(request, u"排期已经被锁定")
            return
        product_list = []
        for one_product in queryset:
            if one_product.status != SaleProduct.SCHEDULE:
                self.message_user(request, u"有未在排期范围内的商品")
                return
            if sale_time != one_product.sale_time.date():
                self.message_user(request, u"有不是同一天的商品")
                return
            sale_time = one_product.sale_time.date()
            product_num += 1
            product_list.append(one_product.id)
            # 新建排期detail
            one_detail, already_cun = SaleProductManageDetail.objects.get_or_create(schedule_manage=mgr_p,
                                                                       sale_product_id=one_product.id)
            one_detail.name = one_product.title
            one_detail.today_use_status = SaleProductManageDetail.NORMAL
            one_detail.pic_path = one_product.pic_url
            one_detail.product_link = one_product.product_link
            try:
                category = one_product.sale_category.full_name
            except:
                category = ""
            one_detail.sale_category = category
            one_detail.save()

        mgr_p.product_num = product_num
        mgr_p.responsible_people_id = request.user.id
        mgr_p.responsible_person_name = request.user.username
        mgr_p.save()
        if state:
            log_action(request.user.id, mgr_p, ADDITION, u'完成排期')
        else:
            log_action(request.user.id, mgr_p, CHANGE, u'修改排期')
        for detail in mgr_p.normal_detail:
            if detail.sale_product_id not in product_list:
                detail.today_use_status = SaleProductManageDetail.DELETE
                detail.save()
        self.message_user(request, u"设置成功")

    schedule_manage_action.short_description = u"排期完成"
    actions = ['voting_action', 'cancel_voting_action', 'schedule_manage_action', 'rejected_action']


admin.site.register(SaleProduct, SaleProductAdmin)


class BuyerGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer_name', 'buyer_group', 'created')
    list_display_links = ('id', 'buyer_name')
    list_filter = ('id', 'buyer_group', 'created')
    search_fields = ['=id', '=buyer_name']


admin.site.register(BuyerGroup, BuyerGroupAdmin)


class SalePraiseAdmin(admin.ModelAdmin):
    list_display = ('id', 'sale_id', 'cus_id', 'praise', 'created', 'pro_from')
    list_display_links = ('id', )
    list_filter = ('pro_from', 'praise')
    search_fields = ['=id', '=sale_id']


admin.site.register(SalePraise, SalePraiseAdmin)


class HotProductAdmin(admin.ModelAdmin):
    list_display = ('pro_pic', 'name', 'sale_pro', 'price', 'hot_value', 'voting', 'status')
    list_display_links = ('name', )
    list_filter = ('voting', 'created')
    search_fields = ['=id', '=name']

    def voting_action(self, request, queryset):
        """  设置爆款投票  取样通过　的产品可以设置参与投票　"""
        no_votigs = queryset.filter(voting=False, status__in=(HotProduct.SELECTED,))
        no_votigs.update(voting=True)
        mes = u"设置选品参与投票完成"
        self.message_user(request, mes)

    def cancel_voting_action(self, request, queryset):
        """  取消爆款投票  """
        votigs = queryset.filter(voting=True)
        votigs.update(voting=False)
        mes = u"取消选品投票设置完成"
        self.message_user(request, mes)


    def pro_pic(self, obj):
        html = u'<img src="{0}" style="height:100px;width=62px">'.format(obj.pic_pth)
        return html

    def sale_pro(self, obj):
        sal_p = obj.proid
        sale_html = u'<a class="btn" target="_blank" href="/admin/supplier/saleproduct/?id={0}">查看选品</a>'.format(sal_p)
        site_url = u'<br><br><a class="btn" target="_blank" href="{0}">查看站点</a>'.format(obj.site_url)
        return sale_html + site_url

    pro_pic.allow_tags = True
    pro_pic.short_description = u"爆款图片"

    sale_pro.allow_tags = True
    sale_pro.short_description = u"特卖选品"


    voting_action.short_description = u"设置爆款投票"
    cancel_voting_action.short_description = u"取消爆款投票"
    actions = ['voting_action', 'cancel_voting_action']

    class Media:
        css = {"all": ("css/hot_pro.css",)}
        js = ("jquery/jquery-1.8.13.min.js",)


admin.site.register(HotProduct, HotProductAdmin)


class SaleProductManageDetailInline(admin.TabularInline):
    model = SaleProductManageDetail
    fields = ('sale_product_id', 'design_take_over', 'design_person', 'name', 'sale_category',
              'product_link', 'material_status', 'design_complete', 'is_promotion', 'today_use_status',
              "order_weight")

    extra = 3
    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + (
                'sale_product_id', 'name', 'design_person', 'design_take_over', 'pic_path',
                'sale_category', 'product_link', 'material_status','today_use_status')
        return self.readonly_fields




class SaleProductManageAdmin(admin.ModelAdmin):
    list_display = ('sale_time', 'product_num', 'schedule_type', 'responsible_person_name', 'lock_status', 'created', 'modified')
    inlines = [SaleProductManageDetailInline]
    list_filter = (('sale_time', DateFieldListFilter), 'schedule_type')
    search_fields = ['product_num', 'responsible_person_name']
    date_hierarchy = 'sale_time'

    def custom_product_list(self, obj):
        product_list = obj.product_list
        result_str = ""
        for k, v in product_list.items():
            result_str += k + ":" + v + "\n"
        return u'<pre style="width:300px;white-space: pre-wrap;word-break:break-all;">{0}</pre>'.format(result_str)
    custom_product_list.allow_tags = True
    custom_product_list.short_description = "商品列表"

    def get_form(self, request, obj=None, **kwargs):
        form = super(SaleProductManageAdmin, self).get_form(request, obj=obj, **kwargs)
        if obj and obj.sale_suppliers.exists():
            form.base_fields['sale_suppliers'].queryset = obj.sale_suppliers.all()
        else:
            form.base_fields['sale_suppliers'].queryset = form.base_fields['sale_suppliers'].queryset.none()
        return form


admin.site.register(SaleProductManage, SaleProductManageAdmin)


class SaleProductManageDetailAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sale_product_id',
        'pic_path_show',
        'order_weight'
    )
    list_filter = ('sale_category', 'schedule_manage')
    ordering = ('order_weight', )

    def pic_path_show(self, obj):
        return u'<img src="{0}" with="40px" height="70px"">'.format(obj.pic_path)

    pic_path_show.allow_tags = True
    pic_path_show.short_description = "图片"

admin.site.register(SaleProductManageDetail, SaleProductManageDetailAdmin)


class SupplierFigureAdmin(admin.ModelAdmin):
    list_display = (
        'supplier',
        'schedule_num',
        'no_pay_num',
        'pay_num',
        'cancel_num',
        'out_stock_num',
        'return_good_num',
        'return_good_rate',
        'payment',
        'cancel_amount',
        'out_stock_amount',
        'return_good_amount',
        'avg_post_days'
    )
    list_filter = ('created', 'modified')
    search_fields = ['supplier__supplier_name', ]
    readonly_fields = ['supplier']

admin.site.register(SupplierFigure, SupplierFigureAdmin)


class CategoryPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'category_info',
        'preferences',
        'is_default',
        'created')
    list_filter = ('created', 'modified', 'category')
    search_fields = ['category__name', ]
    # readonly_fields = ['category']

    def category_info(self, obj):
        return obj.__unicode__()

    category_info.allow_tags = True
    category_info.short_description = "类别"


admin.site.register(CategoryPreference, CategoryPreferenceAdmin)


class PreferencePoolAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'unit',
        'categorys',
        'is_sku',
        'preference_value',
        'created')
    search_fields = ['name', ]
    list_filter = ['is_sku']

admin.site.register(PreferencePool, PreferencePoolAdmin)
