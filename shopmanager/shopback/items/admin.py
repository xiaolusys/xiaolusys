# -*- coding:utf-8 -*-
import json
import urllib
import datetime, time
import cStringIO as StringIO
from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.db import models
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.forms import TextInput, Textarea
from django.db.models.signals import post_save
from core.utils.modelutils import get_class_fields
from shopback.items.models import (Item, Product, ProductSku, ProductLocation,
                                   ItemNumTaskLog, SkuProperty, ProductDaySale,
                                   ProductScanStorage, ImageWaterMark)
from shopback.trades.models import MergeTrade, MergeOrder
from shopback.users.models import User
from shopback.categorys.models import ProductCategory
from django.db.models import F
# from shopback.purchases import getProductWaitReceiveNum
from shopback import paramconfig as pcfg
from core.options import log_action, ADDITION, CHANGE
from shopback.items import permissions as perms
from core.admin import ApproxAdmin
from shopback.items.forms import ProductModelForm
from core.filters import DateFieldListFilter
from shopback.items.filters import ChargerFilter, DateScheduleFilter, GroupNameFilter, CategoryFilter, \
    ProductVirtualFilter, ProductStatusFilter, ProductCategoryFilter
from common.utils import gen_cvs_tuple, CSVUnicodeWriter, update_model_fields
from flashsale.pay.models import Productdetail
from flashsale.pay.forms import ProductdetailForm
from shopback.items.models import ProductSkuStats, ProductSkuSaleStats
from shopback.items.models import InferiorSkuStats
from shopback.items.filters import ProductSkuStatsSupplierIdFilter, ProductSkuStatsSupplierNameFilter, \
    ProductSkuStatsUnusedStockFilter, ProductWareByFilter
from flashsale.dinghuo.models import OrderDraft
from flashsale.dinghuo.models_user import MyUser, MyGroup
from django.contrib.auth.models import User as DjangoUser
from django.forms.models import model_to_dict
from flashsale.dinghuo import functions2view

from flashsale.dinghuo.models import ReturnGoods, RGDetail
from supplychain.supplier.models import SaleProduct, SaleSupplier
from shopback.warehouse import WARE_NONE, WARE_GZ, WARE_SH, WARE_CHOICES
import logging

logger = logging.getLogger('django.request')


class ProductSkuInline(admin.TabularInline):
    model = ProductSku
    fields = ('outer_id', 'properties_name', 'properties_alias', 'quantity',
              'warn_num', 'remain_num', 'wait_post_num', 'reduce_num',
              'lock_num', 'cost', 'std_sale_price', 'agent_price', 'sync_stock',
              'is_assign', 'is_split', 'is_match', 'post_check', 'barcode',
              'status', 'buyer_prompt', "sku_inferior_num")

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '10'})},
        models.FloatField: {'widget': TextInput(attrs={'size': '8'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 2,
                                                     'cols': 20})},
    }

    def get_readonly_fields(self, request, obj=None):
        if not perms.has_change_product_skunum_permission(request.user):
            return self.readonly_fields + ('quantity', 'warn_num', 'lock_num',
                                           'wait_post_num', 'is_split')
        return self.readonly_fields


class ProductdetailInline(admin.StackedInline):
    model = Productdetail
    form = ProductdetailForm

    #     fields = ('head_imgs', 'content_imgs',
    #               ('is_seckill', 'is_recommend', 'is_sale', 'order_weight',
    #                'mama_discount', 'buy_limit', 'per_limit', 'rebeta_scheme_id'),
    #               ('material', 'color'), ('note', 'wash_instructions'))
    fieldsets = (('题头图内容图及商品参数:', {
        'classes': ('collapse',),
        'fields':
            ('head_imgs', 'content_imgs',
             ('material', 'color'), ('note', 'wash_instructions'))
    }),
                 ('商品销售策略设置', {
                     'classes': ('expand',),
                     'fields':
                         (('is_seckill', 'is_recommend', 'is_sale', 'order_weight', 'mama_discount', 'buy_limit',
                           'per_limit', 'rebeta_scheme_id'),)
                 }),)

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '50'})},
    }


class ItemAdmin(admin.ModelAdmin):
    list_display = ('num_iid', 'user', 'outer_id', 'type', 'category', 'title',
                    'price', 'has_showcase', 'sync_stock', 'with_hold_quantity',
                    'delivery_time', 'list_time', 'last_num_updated',
                    'approve_status', 'status')
    list_display_links = ('num_iid', 'title')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'last_num_updated'
    # ordering = ['created_at']

    list_filter = ('user', 'has_showcase', 'sync_stock', 'approve_status')
    search_fields = ['num_iid', 'outer_id', 'title']


admin.site.register(Item, ItemAdmin)

from flashsale.dinghuo.models import OrderDetail


class ProductAdmin(ApproxAdmin):
    #     storage_chargers = []

    form = ProductModelForm
    list_per_page = 25

    list_display = ('id', 'outer_id_link', 'pic_link', 'collect_num',
                    'category_select', 'remain_num', 'wait_post_num',
                    'lock_num', 'wait_receive_num', 'cost', 'std_sale_price',
                    'agent_price', 'modelproduct_link', 'sync_stock', 'is_watermark',
                    'sale_time_select', 'sale_charger', 'ware_select',
                    'district_link', 'shelf_status')  # 'charger_select',

    list_display_links = ('id',)
    # list_editable = ('name',)

    date_hierarchy = 'sale_time'
    #     ordering = ['created','']

    list_filter = ('shelf_status',
                   'status',
                   ('sale_time', DateScheduleFilter),
                   'ware_by',
                   'is_flatten',
                   'sync_stock',
                   'is_split',
                   'is_match',
                   'is_assign',  # ChargerFilter,
                   'is_verify',
                   'details__is_seckill',
                   'details__is_recommend',
                   ('created', DateFieldListFilter),
                   CategoryFilter,
                   GroupNameFilter)

    search_fields = ['=id', '^outer_id', '^name', '=barcode', '=sale_charger',
                     '=storage_charger', '=model_id']

    def outer_id_link(self, obj):

        try:
            product_detail = obj.details
        except:
            product_detail = None
        head_img_url = product_detail and product_detail.head_imgs.split('\n')[0] or Product.NO_PIC_PATH
        style_css = ""
        if obj.status == obj.DELETE:
            style_css = "text-decoration:line-through;"
        elif obj.status == obj.REMAIN:
            style_css = "border:1px solid grey;"
        return u'<p style="%s">%s</p><img src="%s?imageMogr2/thumbnail/100/format/jpg/quality/90" width="50px" height="40px" />' % (
            style_css, obj.outer_id, head_img_url)

    outer_id_link.allow_tags = True
    outer_id_link.short_description = u"商品编码(题头图)"

    def pic_link(self, obj):

        abs_pic_url = obj.pic_path or Product.NO_PIC_PATH

        str_list = []
        str_list.append('<a href="/items/product/%d/" target="_blank">' %
                        obj.id)
        str_list.append(
            '<img src="%s?imageMogr2/thumbnail/100/format/jpg/quality/90" width="100px" height="80px" title="%s"/>'
            % (abs_pic_url, obj.name))
        style_css = ""
        if obj.status == obj.DELETE:
            style_css = "text-decoration:line-through;"
        elif obj.status == obj.REMAIN:
            style_css = "border:1px solid grey;"
        str_list.append('<p><span style="%s">%s</span></p>' % (style_css, obj.name or u'--'))
        return ''.join(str_list)

    pic_link.allow_tags = True
    pic_link.short_description = u"商品图片"

    def district_link(self, obj):
        corresponding_list = []
        orderdetails = OrderDetail.objects.filter(
            product_id=obj.id).values("orderlist_id").distinct()
        for orderdetail in orderdetails:
            corresponding_list.append(str(orderdetail['orderlist_id']))
        a = ','.join(corresponding_list)
        if len(a) > 0:
            return u'<a href="/items/product/district/{0}/"' \
                   u' target="_blank" style="display: block;">货位 &gt;&gt;</a>' \
                   u'<br><a href="/sale/dinghuo/statsbypid/{1}" target="_blank" style="display: block;">订货单&gt;&gt;</a>' \
                   u'<br><a href="/items/get_sku/?search_input={2}" target="_blank" style="display: block;">尺码表&gt;&gt;</a>'.format(
                obj.id, obj.id, obj.outer_id)
        else:
            return u'<a href="/items/product/district/{0}/" target="_blank" style="display: block;">货位 &gt;&gt;</a>' \
                   u'<br><a href="/items/get_sku/?search_input={1}" target="_blank" style="display: block;">尺码表&gt;&gt;</a>'.format(
                obj.id, obj.outer_id)

    district_link.allow_tags = True
    district_link.short_description = u"附加信息>>"

    def wait_receive_num(self, obj):
        from flashsale.dinghuo.options import getProductOnTheWayNum
        wrNum = getProductOnTheWayNum(obj.id, start_time=obj.sale_time)
        if (obj.collect_num + wrNum) < obj.wait_post_num:
            return u'<div style="color:white;background-color:red;">%d</div>' % wrNum
        else:
            return u'<div style="color:white;background-color:green;">%d</div>' % wrNum

    wait_receive_num.allow_tags = True
    wait_receive_num.short_description = u"在途数"

    def modelproduct_link(self, obj):
        return '<a href="%s" target="_blank">%s</a>'%('/admin/pay/modelproduct/%s/'%obj.model_id, obj.model_id)

    modelproduct_link.allow_tags = True
    modelproduct_link.short_description = u"款式ID"

    def get_category_list(self):
        if not hasattr(self, '_category_list_'):
            categorys = ProductCategory.objects.filter()
            self._category_list_ = [(cat.cid, str(cat)) for cat in categorys]
        return self._category_list_

    def category_select(self, obj):
        categorys = self.get_category_list()
        cat_list = ["<select class='category_select' pid='%s'>" % obj.id]
        cat_list.append("<option value=''>-------------</option>")

        for cat_cid, cat_name in categorys:
            if obj.category and obj.category.cid == cat_cid:
                cat_list.append("<option value='%s' selected>%s</option>" %
                                (cat_cid, cat_name))
                continue

            cat_list.append("<option value='%s'>%s</option>" % (cat_cid, cat_name))
        cat_list.append("</select>")

        return "".join(cat_list)

    category_select.allow_tags = True
    category_select.short_description = u"所属类目"

    def ware_select(self, obj):
        wares = WARE_CHOICES
        cat_list = ["<select class='ware_select' pid='%s'>" % obj.id]
        cat_list.append("<option value=''>-------------</option>")

        for cat in wares:
            if obj.ware_by is not None and obj.ware_by == cat[0]:
                cat_list.append("<option value='%s' selected>%s</option>" %
                                (cat[0], cat[1]))
                continue
            cat_list.append("<option value='%s'>%s</option>" % (cat[0], cat[1]))
        cat_list.append("</select>")

        return "".join(cat_list)

    ware_select.allow_tags = True
    ware_select.short_description = u"所属仓库"

    #     def purchase_select(self, obj):
    #         sale_charger = obj.sale_charger
    #         systemuesr = DjangoUser.objects.filter(username=sale_charger)
    #         if systemuesr.count() <= 0:
    #             return "找不到采购员"
    #         groups = MyGroup.objects.all()
    #         myuser = MyUser.objects.filter(user_id=systemuesr[0].id)
    #         if len(sale_charger) > 0 and groups.count() > 0:
    #             group_list = ["<select class='purchase_charger_select' cid='%s'>"%systemuesr[0].id]
    #             group_list.append("<option value=''>---------------</option>")
    #             for group in groups:
    #                 if myuser.count() > 0 and myuser[0].group_id == group.id:
    #                     group_list.append("<option value='%s' selected>%s</option>" % (group.id, group.name))
    #                     continue
    #                 group_list.append("<option value='%s'>%s</option>" % (group.id, group.name))
    #             group_list.append("</select>")
    #             return "%s"%sale_charger+"".join(group_list)
    #
    #
    #     purchase_select.allow_tags = True
    #     purchase_select.short_description = u"所属采购组"

    # 选择上架时间
    def sale_time_select(self, obj):
        sale_time = obj.sale_time
        display_text = u'<input type="text" id="{0}" readonly="true" style="display: block;" class="select_saletime form-control datepicker" name={1} value="{1}"/>'
        if obj.sale_product != 0:
            display_text += u'<br><a href="/admin/supplier/saleproduct/?id={2}" target="_blank" style="display: block;">选品列表&gt;&gt;</a>'
        s = display_text.format(obj.id, sale_time, obj.sale_product)
        return s

    sale_time_select.allow_tags = True
    sale_time_select.short_description = u"上架时间"

    def get_storage_chargers(self):
        if not hasattr(self, '_storage_chargers_list_'):
            self._storage_chargers_list_ = list(User.objects.filter(is_staff=True,
                    groups__name=u'仓管员').values_list('username',flat=True))
        return self._storage_chargers_list_

    def charger_select(self, obj):
        username_list = self.get_storage_chargers()
        if len(username_list) > 0:
            cat_list = ["<select class='charger_select' cid='%s'>" % obj.id]
            cat_list.append("<option value=''>---------------</option>")
            for username in username_list:
                if obj and obj.storage_charger == username:
                    cat_list.append("<option value='%s' selected>%s</option>" %
                                    (username, username))
                    continue
                cat_list.append("<option value='%s'>%s</option>" %
                                (username, username))
            cat_list.append("</select>")
            return "".join(cat_list)
        else:
            return obj.storage_charger and '[%s]' % [obj.storage_charger] or '[-]'

    charger_select.allow_tags = True
    charger_select.short_description = u"所属仓管员"

    inlines = [ProductdetailInline, ProductSkuInline]

    # --------设置页面布局----------------
    fieldsets = (('商品基本信息:', {
                    'classes': ('expand',),
                    'fields':
                        (('outer_id', 'category'), ('name', 'pic_path'),
                         ('collect_num', 'warn_num', 'remain_num', 'wait_post_num',
                          'reduce_num'),
                         ('lock_num', 'inferior_num', 'std_purchase_price', 'staff_price'),
                         ('sale_time', 'upshelf_time', 'offshelf_time'),
                         ('cost', 'std_sale_price', 'agent_price'),
                         ('status', 'shelf_status', 'model_id', 'sale_product', 'ware_by'))
                }),
                ('商品系统设置:', {
                     'classes': ('collapse',),
                     'fields': (('weight', 'sync_stock', 'is_assign','is_split', 'is_match', 'post_check', 'is_verify',
                                 'is_watermark', 'is_flatten'), ('barcode', 'match_reason'),
                                ('sale_charger', 'storage_charger'),
                                ('buyer_prompt', 'memo'))
                 }),)

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': 64,
                                                      'maxlength': '256',})},
        models.FloatField: {'widget': TextInput(attrs={'size': 24})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4,
                                                     'cols': 40})},
    }

    class Media:
        css = {"all": (
            "admin/css/forms.css", "css/admin/dialog.css",
            "css/admin/common.css", "jquery/jquery-ui-1.10.1.css",
            "jquery-timepicker-addon/timepicker/jquery-ui-timepicker-addon.css")
        }
        js = (
            "js/admin/adminpopup.js", "js/item_change_list.js",
            "jquery/jquery-ui-1.8.13.min.js",
            "jquery-timepicker-addon/timepicker/jquery-ui-timepicker-addon.js",
            "jquery-timepicker-addon/js/jquery-ui-timepicker-zh-CN.js")

    def get_readonly_fields(self, request, obj=None):

        if not perms.has_change_product_skunum_permission(request.user):
            return self.readonly_fields + (
                'model_id', 'sale_product', 'collect_num', 'warn_num',
                'lock_num', 'inferior_num', 'wait_post_num', 'sale_charger',
                'storage_charger', 'shelf_status', 'status', 'is_flatten')
        return self.readonly_fields

    def get_actions(self, request):

        user = request.user
        actions = super(ProductAdmin, self).get_actions(request)

        if user.is_superuser:
            return actions

        valid_actions = set([])
        if user.has_perm('items.change_product_shelf'):
            valid_actions.add('weixin_product_action')
            valid_actions.add('upshelf_product_action')
            valid_actions.add('downshelf_product_action')

        if user.has_perm('items.sync_product_stock'):
            valid_actions.add('sync_items_stock')
            valid_actions.add('sync_purchase_items_stock')
            valid_actions.add('cancel_syncstock_action')
            valid_actions.add('active_syncstock_action')

        if user.has_perm('items.regular_product_order'):
            valid_actions.add('cancle_orders_out_stock')
            valid_actions.add('cancel_syncstock_action')
            valid_actions.add('regular_saleorder_action')
            valid_actions.add('deliver_saleorder_action')

        if user.has_perm('items.export_product_info'):
            valid_actions.add('export_prodsku_info_action')

        if user.has_perm('items.create_product_purchase'):
            valid_actions.add('create_saleproduct_order')
            valid_actions.add('create_refund_good')

        if user.has_perm('items.invalid_product_info'):
            valid_actions.add('invalid_product_action')

        valid_actions.add('update_quantity2remain_action')
        unauth_actions = []
        for action in actions.viewkeys():
            action_ss = str(action)
            if action_ss not in valid_actions:
                unauth_actions.append(action_ss)

        for action in unauth_actions:
            del actions[action]
        return actions

    def response_add(self, request, obj, post_url_continue='../%s/'):

        if not obj.sale_charger:
            obj.sale_charger = request.user.username
            obj.save()

        return super(ProductAdmin,
                     self).response_add(request,
                                        obj,
                                        post_url_continue=post_url_continue)

    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        #         if perms.has_change_product_skunum_permission(request.user):
        #             groups = Group.objects.filter(name=u'仓管员')
        #             if groups.count() > 0:
        #                 self.storage_chargers = groups[0].user_set.filter(is_staff=True)

        return super(ProductAdmin, self).get_changelist(request, **kwargs)

    def queryset(self, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = self.model._default_manager.get_queryset()
        # TODO: this should be handled by some parameter to the ChangeList.
        if not request.user.is_superuser:
            qs = qs.exclude(status=pcfg.DELETE)

        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    # 更新用户线上商品入库
    def sync_items_stock(self, request, queryset):

        from shopback.items.tasks import updateUserProductSkuTask, updateItemNum
        users = User.objects.filter(status=pcfg.NORMAL)
        dt = datetime.datetime.now()
        sync_items = []
        for prod in queryset:
            pull_dict = {'outer_id': prod.outer_id, 'name': prod.name}
            try:
                items = Item.objects.filter(outer_id=prod.outer_id)
                # 更新商品信息
                for item in items:
                    Item.get_or_create(item.user.visitor_id,
                                       item.num_iid,
                                       force_update=True)

                items = items.filter(approve_status=pcfg.ONSALE_STATUS)
                if items.count() < 1:
                    raise Exception(u'请确保商品在售')

                for u in users:
                    # 更新商品线上SKU状态
                    updateUserProductSkuTask(
                        user_id=u.visitor_id,
                        outer_ids=[i.outer_id for i in items if i.outer_id])
                # 更新商品及SKU库存
                for item in items:
                    updateItemNum(item.user.visitor_id, item.num_iid)
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
                pull_dict['success'] = False
                pull_dict['errmsg'] = exc.message or '%s' % exc
            else:
                pull_dict['success'] = True
            sync_items.append(pull_dict)

        return render_to_response('items/product_action.html',
                                  {'prods': sync_items,
                                   'action_name': u'更新线上库存'},
                                  context_instance=RequestContext(request),
                                  content_type="text/html")

    sync_items_stock.short_description = u"同步淘宝线上库存"

    # 作废商品
    def invalid_product_action(self, request, queryset):

        uninvalid_qs = queryset.filter(models.Q(collect_num__gt=0) | models.Q(
            wait_post_num__gt=0) | models.Q(shelf_status=Product.UP_SHELF))
        if uninvalid_qs.count() > 0:
            for p in uninvalid_qs:
                msg_list = ['商品编码：%s，不能作废原因:' % p.outer_id]
                if p.collect_num > 0:
                    msg_list.append('库存不为０')
                if p.wait_post_num > 0:
                    msg_list.append('待发数不为０')
                if p.shelf_status == Product.UP_SHELF:
                    msg_list.append('商品未下架')
                self.message_user(request, u"XXXXXX:%s" % (','.join(msg_list)))

            return HttpResponseRedirect(request.get_full_path())

        if queryset.count() >= 25:
            self.message_user(request, u"*********作废的商品数不能超过24个************")
            return HttpResponseRedirect(request.get_full_path())

        product_ids = ','.join([p.outer_id for p in queryset])
        origin_url = request.get_full_path()

        return render_to_response('items/product_delete.html',
                                  {'product_ids': product_ids,
                                   'products': queryset,
                                   'origin_url': origin_url},
                                  context_instance=RequestContext(request),
                                  content_type="text/html")

    invalid_product_action.short_description = u"作废库存商品（批量）"

    # 更新用户线上商品入库
    def sync_purchase_items_stock(self, request, queryset):

        from shopback.items.tasks import updatePurchaseItemNum
        from shopback.fenxiao.models import FenxiaoProduct

        sync_items = []
        for prod in queryset:
            pull_dict = {'outer_id': prod.outer_id, 'name': prod.name}
            try:
                items = FenxiaoProduct.objects.filter(outer_id=prod.outer_id,
                                                      status=pcfg.UP_STATUS)

                if items.count() < 1:
                    raise Exception(u'请确保商品在售')

                # 更新商品及SKU库存
                for item in items:
                    FenxiaoProduct.get_or_create(item.user.visitor_id,
                                                 item.pid,
                                                 force_update=True)

                    updatePurchaseItemNum(item.user.visitor_id, item.pid)
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
                pull_dict['success'] = False
                pull_dict['errmsg'] = exc.message or '%s' % exc
            else:
                pull_dict['success'] = True
            sync_items.append(pull_dict)

        return render_to_response('items/product_action.html',
                                  {'prods': sync_items,
                                   'action_name': u'更新分销线上库存'},
                                  context_instance=RequestContext(request),
                                  content_type="text/html")

    sync_purchase_items_stock.short_description = u"同步分销商品库存"

    def get_product_logsign(self, product):
        return '库存数={0},待发数={1},预留数={2},锁定数={3}'.format(
            product.collect_num, product.wait_post_num, product.remain_num,
            product.wait_post_num)

    # 更新商品库存数至预留数
    def update_quantity2remain_action(self, request, queryset):

        #         downshelfs = queryset.filter(shelf_status=Product.DOWN_SHELF)
        #         upshelfs   = queryset.filter(shelf_status=Product.UP_SHELF)
        p_count = queryset.count()
        for product in queryset:
            product.normal_skus.update(remain_num=models.F('quantity'))
            log_sign = self.get_product_logsign(product)
            log_action(request.user.id, product, CHANGE,
                       u'库存更新预留数:%s' % log_sign)
            if product.normal_skus.count() == 0:
                continue
            product_sku = product.normal_skus[0]
            post_save.send(sender=ProductSku, instance=product_sku, created=False)

        self.message_user(request, u"已成功更新%s个商品的预留数!" % p_count)
        #         self.message_user(request,u"有%s个商品因已上架没有更新预留数!"%upshelfs.count())
        return HttpResponseRedirect(request.get_full_path())

    update_quantity2remain_action.short_description = u"更新商品库存为预留数"

    # 取消该商品缺货订单
    def cancle_orders_out_stock(self, request, queryset):

        sync_items = []
        for prod in queryset:
            pull_dict = {'outer_id': prod.outer_id, 'name': prod.name}
            try:
                orders = MergeOrder.objects.filter(outer_id=prod.outer_id,
                                                   out_stock=True)
                for order in orders:
                    order.out_stock = False
                    order.save()
                    log_action(request.user.id, order.merge_trade, CHANGE,
                               u'取消子订单（%d）缺货' % order.id)
            except Exception, exc:
                pull_dict['success'] = False
                pull_dict['errmsg'] = exc.message or '%s' % exc
            else:
                pull_dict['success'] = True
            sync_items.append(pull_dict)

        return render_to_response('items/product_action.html',
                                  {'prods': sync_items,
                                   'action_name': u'取消商品对应订单缺货状态'},
                                  context_instance=RequestContext(request),
                                  content_type="text/html")

    cancle_orders_out_stock.short_description = u"取消订单商品缺货"

    # 创建订货单
    def create_saleproduct_order(self, request, queryset):

        user = request.user
        orderDrAll = OrderDraft.objects.all().filter(buyer_name=user)
        productres = []
        for p in queryset:
            product_dict = model_to_dict(p)
            product_dict['prod_skus'] = []
            guiges = ProductSku.objects.filter(product_id=p.id).exclude(
                status=u'delete')
            for guige in guiges:
                sku_dict = model_to_dict(guige)
                sku_dict['name'] = guige.name
                sku_dict[
                    'wait_post_num'] = functions2view.get_lack_num_by_product(
                    p, guige)
                product_dict['prod_skus'].append(sku_dict)
            productres.append(product_dict)
        return render_to_response("dinghuo/addpurchasedetail.html",
                                  {"productRestult": productres,
                                   "drafts": orderDrAll},
                                  context_instance=RequestContext(request))

    create_saleproduct_order.short_description = u"创建特卖商品订货单"

    # 取消商品库存同步（批量）
    def active_syncstock_action(self, request, queryset):

        for p in queryset:
            p.sync_stock = True
            p.save()

        self.message_user(request, u"已成功设置%s个商品库存同步!" % queryset.count())

        return HttpResponseRedirect(request.get_full_path())

    active_syncstock_action.short_description = u"设置商品库存同步"

    def cancel_syncstock_action(self, request, queryset):
        """ 取消商品库存同步（批量） """
        count = queryset.count()
        for p in queryset:
            p.sync_stock = False
            p.save()

        self.message_user(request, u"已成功取消%s个商品库存同步!" % count)

        return HttpResponseRedirect(request.get_full_path())

    cancel_syncstock_action.short_description = u"取消商品库存同步"

    def regular_saleorder_action(self, request, queryset):
        """ 订单商品定时提醒（批量） """
        remind_time = datetime.datetime.now() + datetime.timedelta(days=7)
        outer_ids = [p.outer_id for p in queryset]
        mos = MergeOrder.objects.filter(
            outer_id__in=outer_ids,
            merge_trade__sys_status__in=(MergeTrade.WAIT_PREPARE_SEND_STATUS,
                                         MergeTrade.WAIT_AUDIT_STATUS))
        merge_trades = set([o.merge_trade for o in mos])
        effect_num = 0
        for t in merge_trades:
            if (t.status == pcfg.WAIT_SELLER_SEND_GOODS and not t.out_sid and
                        t.prod_num == 1):
                t.sys_status = MergeTrade.REGULAR_REMAIN_STATUS
                t.remind_time = remind_time
                t.save()
                effect_num += 1
                log_action(request.user.id, t, CHANGE,
                           u'定时(%s)提醒' % remind_time)

        self.message_user(request, u"已成功设置%s个订单定时提醒!" % effect_num)

        return HttpResponseRedirect(request.get_full_path())

    regular_saleorder_action.short_description = u"定时商品订单七日"

    def deliver_saleorder_action(self, request, queryset):
        """ 订单商品定时释放（批量） """
        outer_ids = [p.outer_id for p in queryset]
        mos = (MergeOrder.objects.filter(
            outer_id__in=outer_ids,
            merge_trade__sys_status=pcfg.REGULAR_REMAIN_STATUS)
               .order_by('merge_trade__prod_num', 'merge_trade__has_merge'))

        from shopback.items.service import releaseRegularOutstockTrade
        num_maps = {}
        merge_trades = set([o.merge_trade for o in mos])
        for t in merge_trades:
            trade = releaseRegularOutstockTrade(t, num_maps)
            if trade.sys_status in (pcfg.WAIT_AUDIT_STATUS,
                                    pcfg.WAIT_PREPARE_SEND_STATUS):
                log_action(request.user.id, trade, CHANGE, u'取消定时提醒')
        self.message_user(request, u"已成功取消%s个订单定时提醒!" % len(merge_trades))
        return HttpResponseRedirect(request.get_full_path())

    deliver_saleorder_action.short_description = u"释放商品定时订单"

    def weixin_product_action(self, request, queryset):
        """  商品库存 """
        if queryset.count() > 25:
            self.message_user(request, u"*********选择更新的商品数不能超过25个************")
            return HttpResponseRedirect(request.get_full_path())

        product_ids = ','.join([str(p.id) for p in queryset])

        absolute_uri = request.build_absolute_uri()
        params = {'format': 'html',
                  'product_ids': product_ids,
                  'next': absolute_uri}
        url_params = urllib.urlencode(params)

        return HttpResponseRedirect(reverse('weixin_product_modify') + '?' +
                                    url_params)

    weixin_product_action.short_description = u"更新微信商品库存信息"

    def upshelf_product_action(self, request, queryset):
        """ 库存商品上架（批量） """
        qs_outer_ids = [p.outer_id for p in queryset]
        upshelf_qs = queryset.filter(shelf_status=Product.DOWN_SHELF,
                                     status=Product.NORMAL)
        outer_ids = [p.outer_id for p in upshelf_qs]
        from shopapp.weixin.models import WXProduct
        from shopapp.weixin.tasks import task_Mod_Merchant_Product_Status

        try:
            task_Mod_Merchant_Product_Status(outer_ids, WXProduct.UP_ACTION)
        except Exception, exc:
            self.message_user(request, u"更新错误，微信商品上下架接口异常：%s" % exc.message)

        up_queryset = Product.objects.filter(outer_id__in=qs_outer_ids,
                                             shelf_status=Product.UP_SHELF)
        down_queryset = Product.objects.filter(outer_id__in=qs_outer_ids,
                                               shelf_status=Product.DOWN_SHELF)
        for product in up_queryset:
            log_sign = self.get_product_logsign(product)
            log_action(request.user.id, product, CHANGE, u'上架商品:%s' % log_sign)
        self.message_user(request, u"已成功上架%s个商品,有%s个商品上架失败!" %
                          (up_queryset.count(), down_queryset.count()))
        for product in down_queryset:
            msg = u"xxx商品上架失败：%s" % product.outer_id
            if not product.is_verify:
                msg += u',商品信息未校对'
            if product.status != Product.NORMAL:
                msg += u',商品状态(%s)非正常使用状态' % product.get_status_display()
            self.message_user(request, msg)

        return HttpResponseRedirect(request.get_full_path())

    upshelf_product_action.short_description = u"上架微信商品 (批量)"

    def downshelf_product_action(self, request, queryset):
        """ 库存商品下架（批量） """
        downshelf_qs = queryset.filter(shelf_status=Product.UP_SHELF)
        outer_ids = [p.outer_id for p in downshelf_qs]
        from shopapp.weixin.models import WXProduct
        from shopapp.weixin.tasks import task_Mod_Merchant_Product_Status
        try:
            task_Mod_Merchant_Product_Status(outer_ids, WXProduct.DOWN_ACTION)
        except Exception, exc:
            self.message_user(request, u"更新错误，商品上下架接口异常：%s" % exc.message)

        up_queryset = Product.objects.filter(outer_id__in=outer_ids,
                                             shelf_status=Product.UP_SHELF)
        down_queryset = Product.objects.filter(outer_id__in=outer_ids,
                                               shelf_status=Product.DOWN_SHELF)

        self.message_user(request, u"已成功下架%s个商品,有%s个商品下架失败!" %
                          (down_queryset.count(), up_queryset.count()))
        for product in down_queryset:
            log_sign = self.get_product_logsign(product)
            log_action(request.user.id, product, CHANGE, u'下架商品:%s' % log_sign)

        return HttpResponseRedirect(request.get_full_path())

    downshelf_product_action.short_description = u"下架微信商品 (批量)"

    # 导出商品规格信息
    def export_prodsku_info_action(self, request, queryset):
        """ 导出商品及规格信息 """

        is_windows = request.META['HTTP_USER_AGENT'].lower().find(
            'windows') > -1
        pcsv = []
        pcsv.append((u'商品编码', u'商品名', u'规格编码', u'规格名', u'库存数', u'昨日销量', u'预留库位',
                     u'待发数', u'日出库', u'成本', u'吊牌价', u'库位', u'条码'))
        for prod in queryset:
            skus = prod.pskus.exclude(is_split=True)
            if skus.count() > 0:
                for sku in skus:
                    pcsv.append((prod.outer_id, prod.name, sku.outer_id, sku.name, str(sku.quantity), str(sku.warn_num), \
                                 str(sku.remain_num), str(sku.wait_post_num), str(sku.sale_num), str(sku.cost), \
                                 str(sku.std_sale_price), sku.get_districts_code(), sku.barcode))
            else:
                pcsv.append((prod.outer_id, prod.name, '', '', str(prod.collect_num), str(prod.warn_num), \
                             str(prod.remain_num), str(prod.wait_post_num), str(sku.sale_num), str(prod.cost), \
                             str(prod.std_sale_price), prod.get_districts_code(), prod.barcode))
            pcsv.append(['', '', '', '', '', '', '', '', '', '', '', ''])

        tmpfile = StringIO.StringIO()
        writer = CSVUnicodeWriter(tmpfile,
                                  encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)

        response = HttpResponse(tmpfile.getvalue(),
                                content_type='application/octet-stream')
        tmpfile.close()
        response[
            'Content-Disposition'] = 'attachment; filename=product-sku-info-%s.csv' % str(
            int(time.time()))

        return response

    export_prodsku_info_action.short_description = u"导出商品及规格信息"

    def create_refund_good(self, request, queryset):
        for pro in queryset:
            rg = ReturnGoods()
            rg.product_id = pro.id
            try:
                sale_pro = SaleProduct.objects.get(id=pro.sale_product)
                supplier_id = sale_pro.sale_supplier.id
                if not rg.can_return(supplier_id=supplier_id):
                    break
            except SaleProduct.DoesNotExist:
                supplier_id = 0
            rg.supplier_id = supplier_id  # 找到供应商
            rg.noter = request.user.username
            total_num = 0
            total_price = 0
            rg.save()
            for sku in pro.normal_skus.all():
                return_num = sku.quantity - sku.wait_post_num
                return_num = return_num if return_num > 0 else sku.quantity
                total_num += return_num + sku.sku_inferior_num
                total_price += total_num * sku.cost
                return_good_id = rg.id
                RGDetail.objects.create(skuid=sku.id,
                                        return_goods_id=return_good_id,
                                        num=return_num,
                                        inferior_num=sku.sku_inferior_num,
                                        price=sku.cost)
            rg.return_num = total_num
            rg.sum_amount = total_price
            rg.save()
        self.message_user(request, u'创建成功')

    create_refund_good.short_description = u"生成退货单"

    actions = ['sync_items_stock', 'invalid_product_action',
               'sync_purchase_items_stock', 'weixin_product_action',
               'upshelf_product_action', 'downshelf_product_action',
               'cancle_orders_out_stock', 'active_syncstock_action',
               'cancel_syncstock_action', 'regular_saleorder_action',
               'deliver_saleorder_action', 'export_prodsku_info_action',
               'update_quantity2remain_action', 'create_refund_good',
               'create_saleproduct_order']


admin.site.register(Product, ProductAdmin)


class ProductSkuAdmin(admin.ModelAdmin):
    list_display = ('id', 'outer_id', 'product', 'properties_name',
                    'properties_alias', 'quantity', 'warn_num', 'remain_num',
                    'wait_post_num', 'lock_num', 'cost', 'std_sale_price', 'sync_stock',
                    'is_assign', 'is_split', 'is_match', 'post_check',
                    'district_link', 'status')
    list_display_links = ('outer_id',)
    list_editable = ('quantity',)

    date_hierarchy = 'modified'
    # ordering = ['created_at']

    list_filter = ('status', 'sync_stock', 'is_split', 'is_match', 'is_assign',
                   'post_check')
    search_fields = ['id', 'outer_id', 'product__outer_id', 'properties_name',
                     'properties_alias']

    def district_link(self, obj):
        return u'<a href="%d/" onclick="return showTradePopup(this);">%s</a>' % (
            obj.id, obj.get_districts_code() or u'--')

    district_link.allow_tags = True
    district_link.short_description = "库位"

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '16'})},
        models.FloatField: {'widget': TextInput(attrs={'size': '16'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 2,
                                                     'cols': 25})},
    }

    # --------设置页面布局----------------
    fieldsets = (('商品基本信息:', {
        'classes': ('expand',),
        'fields':
            (('outer_id', 'properties_name', 'properties_alias', 'status'),
             ('quantity', 'warn_num', 'remain_num', 'wait_post_num', 'lock_num', 'weight'),
             ('cost', 'std_purchase_price', 'std_sale_price', 'agent_price',
              'staff_price'), ('sync_stock', 'is_assign', 'is_split', 'is_match',
                               'memo', 'buyer_prompt', "sku_inferior_num"))
    }),)

    # 取消该商品缺货订单
    def cancle_items_out_stock(self, request, queryset):

        sync_items = []
        for prod in queryset:
            pull_dict = {'outer_id': prod.outer_id,
                         'name': prod.properties_name}
            try:
                orders = MergeOrder.objects.filter(
                    outer_id=prod.product.outer_id,
                    outer_sku_id=prod.outer_id,
                    out_stock=True)
                for order in orders:
                    order.out_stock = False
                    order.save()
                    log_action(request.user.id, order.merge_trade, CHANGE,
                               u'取消子订单（%d）缺货' % order.id)
            except Exception, exc:
                pull_dict['success'] = False
                pull_dict['errmsg'] = exc.message or '%s' % exc
            else:
                pull_dict['success'] = True
            sync_items.append(pull_dict)

        return render_to_response('items/product_action.html',
                                  {'prods': sync_items,
                                   'action_name': u'取消规格对应订单缺货状态'},
                                  context_instance=RequestContext(request),
                                  content_type="text/html")

    cancle_items_out_stock.short_description = u"取消规格订单缺货"

    actions = ['cancle_items_out_stock']


admin.site.register(ProductSku, ProductSkuAdmin)


class SkuPropertyAdmin(admin.ModelAdmin):
    list_display = ('num_iid', 'sku_id', 'outer_id', 'properties_name', 'price',
                    'quantity', 'with_hold_quantity', 'sku_delivery_time',
                    'created', 'modified', 'status')
    list_display_links = ('sku_id', 'outer_id')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status',)
    search_fields = ['outer_id', 'sku_id', 'num_iid', 'properties_name']


admin.site.register(SkuProperty, SkuPropertyAdmin)


class ProductLocationAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'sku_id', 'outer_id', 'name', 'outer_sku_id',
                    'properties_name', 'district')
    list_display_links = ('outer_id', 'outer_sku_id')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    search_fields = ['product_id', 'sku_id', 'outer_id', 'outer_sku_id',
                     'district__parent_no']


admin.site.register(ProductLocation, ProductLocationAdmin)


class ItemNumTaskLogAdmin(ApproxAdmin):
    list_display = ('id', 'user_id', 'outer_id', 'sku_outer_id', 'num',
                    'start_at', 'end_at')
    list_display_links = ('outer_id', 'sku_outer_id')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    #     date_hierarchy = 'end_at'

    list_filter = ('user_id', ('end_at', DateFieldListFilter))
    search_fields = ['=id', '=outer_id', '=sku_outer_id']


admin.site.register(ItemNumTaskLog, ItemNumTaskLogAdmin)


class ProductDaySaleAdmin(admin.ModelAdmin):
    list_display = ('day_date', 'user_id', 'product_id', 'sku_id', 'sale_num',
                    'sale_payment', 'confirm_num', 'confirm_payment',
                    'sale_refund')
    list_display_links = ('day_date', 'user_id', 'product_id')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    # date_hierarchy = 'day_date'

    list_filter = ('user_id', ('day_date', DateFieldListFilter))
    search_fields = ['id', 'user_id', 'product_id', 'sku_id']


admin.site.register(ProductDaySale, ProductDaySaleAdmin)


class ProductScanStorageAdmin(admin.ModelAdmin):
    list_display = ('wave_no', 'product_id', 'qc_code', 'sku_code',
                    'product_name', 'barcode', 'scan_num', 'created', 'status')
    list_display_links = ('product_id', 'barcode')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    # date_hierarchy = 'day_date'

    list_filter = ('status', ('created', DateFieldListFilter))
    search_fields = ['product_id', 'qc_code', 'barcode', 'wave_no']

    def get_actions(self, request):

        user = request.user
        actions = super(ProductScanStorageAdmin, self).get_actions(request)

        if not user.has_perm(
                'items.has_delete_permission') and 'delete_selected' in actions:
            del actions['delete_selected']

        return actions

    def queryset(self, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = self.model._default_manager.get_queryset()
        # TODO: this should be handled by some parameter to the ChangeList.
        if not request.user.is_superuser:
            qs = qs.exclude(status=ProductScanStorage.DELETE)

        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    # 取消该商品缺货订单
    def confirm_scan_action(self, request, queryset):

        queryset = queryset.filter(status=ProductScanStorage.WAIT)
        try:
            for prod in queryset:

                if prod.sku_id:
                    product_sku = ProductSku.objects.get(
                        id=prod.sku_id,
                        product=prod.product_id)

                    product_sku.update_quantity(prod.scan_num)

                    product = product_sku.product
                else:
                    product = Product.objects.get(id=prod.product_id)

                    product.update_collect_num(prod.scan_num)

                prod.status = ProductScanStorage.PASS

                prod.save()

                log_action(request.user.id, prod, CHANGE,
                           u'确认入库：%s' % prod.scan_num)

                log_action(request.user.id, product, CHANGE,
                           u'扫描确认入库数：%s' % prod.scan_num)

        except Exception, exc:
            messages.add_message(request, messages.ERROR,
                                 u'XXXXXXXXXXXXXXXXX确认入库异常:%sXXXXXXXXXXXX' %
                                 exc)
        else:
            messages.add_message(request, messages.INFO,
                                 u'==================操作成功==================')

        return HttpResponseRedirect('./')

    confirm_scan_action.short_description = u"确认入库"

    # 取消该商品缺货订单
    def delete_scan_action(self, request, queryset):

        queryset = queryset.filter(status=ProductScanStorage.WAIT)
        try:
            for prod in queryset:
                prod.scan_num = 0
                prod.status = ProductScanStorage.DELETE

                prod.save()

                log_action(request.user.id, prod, CHANGE, u'作废')

        except Exception, exc:
            messages.add_message(request, messages.ERROR,
                                 u'XXXXXXXXXXXXXXXXX作废失败:%sXXXXXXXXXXXX' % exc)
        else:
            messages.add_message(request, messages.INFO,
                                 u'==================已作废==================')

        return HttpResponseRedirect('./')

    delete_scan_action.short_description = u"作废扫描记录"

    # 取消该商品缺货订单
    def export_scan_action(self, request, queryset):
        """ 导出商品及规格信息 """

        is_windows = request.META['HTTP_USER_AGENT'].lower().find(
            'windows') > -1

        pcsv = gen_cvs_tuple(
            queryset,
            fields=['barcode', 'product_id', 'sku_id', 'product_name',
                    'sku_name', 'scan_num', 'created', 'wave_no'],
            title=[u'商品条码', u'商品ID', u'规格ID', u'商品名称', u'规格名', u'扫描数量', u'扫描时间',
                   u'批次号'])

        pcsv[0].insert(1, u'库位')
        pcsv[0].insert(2, u'商品编码')
        pcsv[0].insert(3, u'规格编码')

        for i in range(1, len(pcsv)):
            item = pcsv[i]
            product_id, sku_id = item[1].strip(), item[2].strip()

            product_loc = ''
            try:
                product = Product.objects.get(id=product_id)
            except:
                product = None
            product_sku = None
            if sku_id and sku_id != 'None' and sku_id != '-':
                product_sku = ProductSku.objects.get(id=sku_id)

            item.insert(1, product_sku and product_sku.get_districts_code() or
                        (product and product.get_districts_code() or ''))
            item.insert(2, product and product.outer_id or u'商品未找到!!!')
            item.insert(3, product_sku and product_sku.outer_id or '')

        tmpfile = StringIO.StringIO()
        writer = CSVUnicodeWriter(tmpfile,
                                  encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)

        response = HttpResponse(tmpfile.getvalue(),
                                content_type='application/octet-stream')
        tmpfile.close()
        response[
            'Content-Disposition'] = 'attachment; filename=product-scan-%s.csv' % str(
            int(time.time()))

        return response

    export_scan_action.short_description = u"导出扫描商品数"

    actions = ['confirm_scan_action', 'delete_scan_action',
               'export_scan_action']


admin.site.register(ProductScanStorage, ProductScanStorageAdmin)

from shopback.items.models import ProductSkuContrast, ContrastContent


class ProductSkuContrastAdmin(admin.ModelAdmin):
    list_display = ('product', 'contrast_detail')

    def get_readonly_fields(self, request, obj=None):
        rset = set([])
        if self.readonly_fields:
            rset = set(self.readonly_fields)
        rset.add('product')
        return rset


admin.site.register(ProductSkuContrast, ProductSkuContrastAdmin)


class ProductSkuStatsAdmin(admin.ModelAdmin):
    list_display = (
        'sku_link', 'skucode', 'supplier','product_id_link', 'product_title', 'properties_name_alias',
        'now_quantity', 'old_quantity', 'sold_num_link', 'post_num_link', '_wait_post_num', 'unused_stock_link',
        'adjust_quantity', 'assign_num_link', '_wait_assign_num', '_wait_order_num', 'history_quantity',
        'inbound_quantity_link', 'return_quantity_link', 'rg_quantity_link',
        'district_link', 'created')
    list_display_links = ['sku_link']
    search_fields = ['sku__id', 'product__id', 'product__name', 'product__outer_id']
    #('supplier_id', ProductSkuStatsSupplierIdFilter),                 ('supplier_name', ProductSkuStatsSupplierNameFilter)]
    readonly_fields = [u'id', 'sku', 'product', 'assign_num', 'adjust_quantity', 'history_quantity',
                       'inbound_quantity', 'return_quantity', 'rg_quantity', 'post_num', 'sold_num', 'shoppingcart_num',
                       'waitingpay_num', 'created', 'modified', 'status']
    list_select_related = True
    list_per_page = 50
    list_filter = ['status', ProductSkuStatsUnusedStockFilter, ProductWareByFilter, ProductVirtualFilter, ProductStatusFilter, ProductCategoryFilter]

    SKU_PREVIEW_TPL = (
        '<a href="%(sku_url)s" target="_blank">'
        '%(skucode)s</a>')

    def sku_link(self, obj):
        return obj.sku_id

    sku_link.short_description = 'SKU'

    def lookup_allowed(self, lookup, value):
        if lookup in ['product__name', 'product__outer_id', 'supplier_id', 'supplier_name']:
            return True
        return super(ProductSkuStatsAdmin, self).lookup_allowed(lookup, value)

    def get_search_results(self, request, queryset, search_term):
        import operator
        from django.contrib.admin.utils import lookup_needs_distinct
        custom_search_fields = ['supplier_id', 'supplier_name']
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        use_distinct = False
        search_fields = self.get_search_fields(request)
        custom_condition = {}
        for field in custom_search_fields:
            if field in search_fields:
                custom_condition[field] = request.GET.get(field)
                # search_fields.remove(field)
        if search_fields and search_term:
            orm_lookups = [construct_search(str(search_field))
                           for search_field in search_fields]
            for bit in search_term.split():
                or_queries = [models.Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                queryset = queryset.filter(reduce(operator.or_, or_queries))
            if not use_distinct:
                for search_spec in orm_lookups:
                    if lookup_needs_distinct(self.opts, search_spec):
                        use_distinct = True
                        break
        if custom_condition:
            supplier_id = request.GET.get('supplier_id')
            supplier_name = request.GET.get('supplier_name')
            if supplier_id:
                supplier = SaleSupplier.objects.filter(pk=supplier_id).first()
            elif supplier_name:
                supplier = SaleSupplier.objects.filter(supplier_name=supplier_name).first()
            else:
                supplier = None
            if supplier:
                queryset = queryset.filter(product_id__in=ProductSkuStats.filter_by_supplier(supplier.id))
        return queryset, use_distinct

    def unused_stock_link(self, obj):
        return obj.unused_stock

    unused_stock_link.short_description = u'冗余库存数'
    unused_stock_link.admin_order_field = 'unused_stock'

    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        orderingdict = {'now_quantity': (F('post_num') + F('rg_quantity')
                                         - F('history_quantity') - F('adjust_quantity') - F('inbound_quantity') - F('return_quantity'),
                                         F('history_quantity') + F('adjust_quantity') + F('inbound_quantity') + F('return_quantity') - F(
                                             'post_num') - F('rg_quantity')),
                        'unused_stock': (F('sold_num') + F('rg_quantity')
                                         - F('history_quantity') - F('adjust_quantity') - F('inbound_quantity') - F('return_quantity'),
                                         F('history_quantity') + F('adjust_quantity') + F('inbound_quantity') + F('return_quantity') - F(
                                             'sold_num') - F('rg_quantity')),
                        'wait_assign_num':(F('post_num') + F('assign_num') - F('sold_num'),
                                         F('sold_num') - F('post_num') - F('assign_num'))
                        }
        from django.contrib.admin.views.main import ChangeList, ORDER_VAR, SuspiciousOperation, ImproperlyConfigured,\
            IncorrectLookupParameters

        class StatsOrderChangeList(ChangeList):
            def get_ordering(self, request, queryset):
                params = self.params
                ordering = list(self.model_admin.get_ordering(request) or self._get_default_ordering())
                if ORDER_VAR in params:
                    ordering = []
                    order_params = params[ORDER_VAR].split('.')
                    for p in order_params:
                        try:
                            none, pfx, idx = p.rpartition('-')
                            field_name = self.list_display[int(idx)]
                            order_field = self.get_ordering_field(field_name)
                            if not order_field:
                                continue
                            if order_field in orderingdict:
                                if pfx == '-':
                                    ordering.append(orderingdict[order_field][0])
                                else:
                                    ordering.append(orderingdict[order_field][1])
                            elif order_field.startswith('-') and pfx == "-":
                                ordering.append(order_field[1:])
                            else:
                                ordering.append(pfx + order_field)
                        except (IndexError, ValueError):
                            continue
                ordering.extend(queryset.query.order_by)
                pk_name = self.lookup_opts.pk.name
                if not (set(ordering) & {'pk', '-pk', pk_name, '-' + pk_name}):
                    ordering.append('-pk')
                return ordering

            # def get_queryset(self, request):
            #     (self.filter_specs, self.has_filters, remaining_lookup_params,
            #      filters_use_distinct) = self.get_filters(request)
            #     qs = self.root_queryset
            #     for filter_spec in self.filter_specs:
            #         new_qs = filter_spec.queryset(request, qs)
            #         if new_qs is not None:
            #             qs = new_qs
            #     try:
            #         qs = qs.filter(**remaining_lookup_params)
            #     except (SuspiciousOperation, ImproperlyConfigured):
            #         raise
            #     except Exception as e:
            #         raise IncorrectLookupParameters(e)
            #     if not qs.query.select_related:
            #         qs = self.apply_select_related(qs)
            #     ordering = self.get_ordering(request, qs)
            #     qs = qs.order_by(*ordering)
            #     qs, search_use_distinct = self.model_admin.get_search_results(
            #         request, qs, self.query)
            #     if filters_use_distinct | search_use_distinct:
            #         return qs.distinct()
            #     else:
            #         return qs
        return StatsOrderChangeList

    # def get_queryset(self, request):
    #     """
    #     Returns a QuerySet of all model instances that can be edited by the
    #     admin site. This is used by changelist_view.
    #     """
    #     qs = self.model._default_manager.get_queryset()
    #     # TODO: this should be handled by some parameter to the ChangeList.
    #     ordering = self.get_ordering(request)
    #     if ordering:
    #         qs = qs.order_by(*ordering)
    #     return qs

    def gen_return_goods(self, request, queryset):
        sku_dict = {}
        sku_num = queryset.count()
        for stat in queryset:
            sku_dict[stat.sku_id] = stat.history_quantity + stat.adjust_quantity + stat.inbound_quantity + stat.return_quantity \
                                    - stat.rg_quantity - stat.sold_num
        returns = ReturnGoods.generate(sku_dict, request.user.username)
        self.message_user(request, '本次对%d个SKU执行了退货, 生成了%d个退货单' % (sku_num, len(returns)))
        return HttpResponseRedirect('/admin/dinghuo/returngoods/?status__exact=0')

    gen_return_goods.allow_tags = True
    gen_return_goods.short_description = u'生成退货单'

    def gen_return_goods_by_five(self, request, queryset):
        sku_dict = {}
        sku_num = queryset.count()
        for stat in queryset:
            sku_dict[
                stat.sku_id] = stat.history_quantity + stat.adjust_quantity + stat.inbound_quantity + stat.return_quantity \
                               - stat.rg_quantity - stat.sold_num
        returns = ReturnGoods.generate(sku_dict, request.user.username,days=0)
        self.message_user(request, '本次对%d个SKU执行了退货, 生成了%d个退货单' % (sku_num, len(returns)))
        return HttpResponseRedirect('/admin/dinghuo/returngoods/?status__exact=0')

    gen_return_goods_by_five.allow_tags = True
    gen_return_goods_by_five.short_description = u'从上架起0天后生成退货单'


    def mark_unreturn(self, request, queryset):
        from flashsale.dinghuo.models import UnReturnSku

        for productsku_stat in queryset:
            product = productsku_stat.product
            saleproduct = SaleProduct.objects.get(id=product.sale_product)

            # 清理数据
            rows = UnReturnSku.objects.filter(product=product, sku=productsku_stat.sku)
            if rows:
                row = rows[0]
                row.supplier = saleproduct.sale_supplier
                row.sale_product = saleproduct
                row.status = UnReturnSku.EFFECT
                row.creater = request.user
                row.save()

                for row in rows[1:]:
                    row.delete()
            else:
                unreturn_sku = UnReturnSku(
                    supplier=saleproduct.sale_supplier,
                    sale_product=saleproduct,
                    product=product,
                    sku=productsku_stat.sku,
                    creater=request.user,
                    status=UnReturnSku.EFFECT
                )
                unreturn_sku.save()
        return HttpResponseRedirect(request.get_full_path())

    mark_unreturn.short_description = u'标记不可退货'

    def skucode(self, obj):
        sku = obj.sku
        product = obj.product
        barcode = sku.barcode.strip() or '%s%s' % (product.outer_id.strip(),
                                                 sku.outer_id.strip())
        return self.SKU_PREVIEW_TPL % {
            'sku_url': '/admin/items/productsku/%s/' % str(obj.sku_id),
            'skucode': barcode
        }

    skucode.allow_tags = True
    skucode.short_description = u'sku条码'


    PRODUCT_LINK = (
        '<a href="%(product_url)s" target="_blank">'
        '%(product_title)s</a>')

    def supplier(self, obj):
        supplier = obj.product.get_supplier()
        if supplier:
            return supplier.supplier_name
        return ''
    supplier.short_description = u'供应商'

    def product_id_link(self, obj):
        return ('<a href="%(product_url)s" target="_blank">'
                '%(product_id)s</a>') % {
                   'product_url': '/admin/items/product/?id=%d' % obj.product_sku.product.id,
                   'product_id': obj.product_sku.product.id
               }

    product_id_link.allow_tags = True
    product_id_link.short_description = u'商品ID'

    def sold_num_link(self, obj):
        return ('<a href="%(url)s" target="_blank">%(num)s</a>') % {
            'url': '/admin/pay/saleorder/?status__in=2,3,4,5&sku_id=%s' % obj.sku_id,
            'num': obj.sold_num
        }

    sold_num_link.allow_tags = True
    sold_num_link.short_description = u'购买数'
    sold_num_link.admin_order_field = 'sold_num'

    def post_num_link(self, obj):
        return ('<a href="%(url)s" target="_blank">%(num)s</a>') % {
            'url': '/admin/trades/packageskuitem/?assign_status=2&sku_id=%s' % obj.sku_id,
            'num': obj.post_num
        }

    post_num_link.allow_tags = True
    post_num_link.short_description = u'已发数'
    post_num_link.admin_order_field = 'post_num'

    def assign_num_link(self, obj):
        return ('<a href="%(url)s" target="_blank">%(num)s</a>') % {
            'url': '/admin/trades/packageskuitem/?assign_status=1&sku_id=%s' % obj.sku_id,
            'num': obj.assign_num
        }

    assign_num_link.allow_tags = True
    assign_num_link.short_description = u'分配数'
    assign_num_link.admin_order_field = 'assign_num'

    def inbound_quantity_link(self, obj):
        return ('<a href="%(url)s" target="_blank">%(num)s</a>') % {
            'url': '/admin/dinghuo/orderdetail/?chichu_id=%s' % obj.sku_id,
            'num': obj.inbound_quantity
        }

    inbound_quantity_link.allow_tags = True
    inbound_quantity_link.short_description = u'订货数'
    inbound_quantity_link.admin_order_field = 'inbound_quantity'

    def return_quantity_link(self, obj):
        return obj.return_quantity
        # return ('<a href="%(url)s" target="_blank">%(num)s</a>') % {
        #     'url': '/admin/dinghuo/orderdetail/?chichu_id=1&sku_id=%(sku)s',
        #     'sku': obj.sku_id,
        #     'num': obj.return_quantity
        # }

    # return_quantity_link.allow_tags = True
    return_quantity_link.short_description = u'用户退货数'
    return_quantity_link.admin_order_field = 'return_quantity'

    def rg_quantity_link(self, obj):
        return ('<a href="%(url)s" target="_blank">%(num)s</a>') % {
            'url': '/admin/dinghuo/returngoods/?rg_details__skuid=%s' % obj.sku_id,
            'num': obj.rg_quantity
        }

    rg_quantity_link.allow_tags = True
    rg_quantity_link.short_description = u'仓库退货数'
    rg_quantity_link.admin_order_field = 'rg_quantity'

    def product_title(self, obj):
        return self.PRODUCT_LINK % {
            'product_url': '/admin/items/product/%d/' % obj.product_sku.product.id,
            'product_title': obj.product.name
        }

    product_title.allow_tags = True
    product_title.short_description = u'商品名称'

    def now_quantity(self, obj):
        return obj.realtime_quantity

    now_quantity.short_description = u'实时库存'
    now_quantity.admin_order_field = 'now_quantity'

    def old_quantity(self, obj):
        return obj.product_sku.quantity

    old_quantity.short_description = u'老系统实时库存'

    def properties_name_alias(self, obj):
        return obj.properties_name

    properties_name_alias.short_description = u'规格'

    def _wait_post_num(self, obj):
        return obj.wait_post_num

    _wait_post_num.short_description = u'待发数'

    def _wait_assign_num(self, obj):
        return ('<a href="%(url)s" target="_blank">%(num)s</a>') % {
            'url': '/admin/trades/packageskuitem/?assign_status=0&sku_id=%s' % obj.sku_id,
            'num': obj.wait_assign_num
        }

    _wait_assign_num.allow_tags = True
    _wait_assign_num.short_description = u'待分配数'
    _wait_assign_num.admin_order_field = 'wait_assign_num'
    def _wait_order_num(self, obj):
        return ('<a href="%(url)s" target="_blank">%(num)s</a>') % {
            'url': '/admin/dinghuo/orderdetail/?chichu_id=%s' % obj.sku_id,
            'num': obj.wait_order_num
        }

    _wait_order_num.allow_tags = True
    _wait_order_num.short_description = u'待订货数'

    def district_link(self, obj):
        return u'<a href="%d/" onclick="return showTradePopup(this);">%s</a>' % (
            obj.product_sku.id, obj.product_sku.get_districts_code() or u'--')

    district_link.allow_tags = True
    district_link.short_description = "库位"
    actions = ['gen_return_goods', 'gen_return_goods_by_five', 'mark_unreturn']

    def get_actions(self, request):
        actions = super(ProductSkuStatsAdmin, self).get_actions(request)
        actions.pop('delete_selected')
        return actions


admin.site.register(ProductSkuStats, ProductSkuStatsAdmin)


class InferiorSkuStatsAdmin(admin.ModelAdmin):
    list_display = (
        'sku_link', 'skucode', 'product_id_link', 'product_title', 'properties_name_alias',
        'now_quantity', 'history_quantity', 'inbound_quantity_link', 'return_quantity_link',
        'rg_quantity_link', 'created')
    search_fields = ['sku__id', 'product__id', 'product__name', 'product__outer_id']
    list_select_related = True
    list_per_page = 50
    list_filter = []
    SKU_PREVIEW_TPL = (
        '<a href="%(sku_url)s" target="_blank">'
        '%(skucode)s</a>')

    def sku_link(self, obj):
        return obj.sku_id

    sku_link.short_description = 'SKU'

    def skucode(self, obj):
        return self.SKU_PREVIEW_TPL % {
            'sku_url': '/admin/items/productsku/%s/' % str(obj.sku_id),
            'skucode': obj.sku.BARCODE
        }

    skucode.allow_tags = True
    skucode.short_description = u'sku条码'

    PRODUCT_LINK = (
        '<a href="%(product_url)s" target="_blank">'
        '%(product_title)s</a>')

    def product_id_link(self, obj):
        return ('<a href="%(product_url)s" target="_blank">'
                '%(product_id)s</a>') % {
                   'product_url': '/admin/items/product/?id=%d' % obj.sku.product.id,
                   'product_id': obj.sku.product.id
               }

    product_id_link.allow_tags = True
    product_id_link.short_description = u'商品ID'

    def inbound_quantity_link(self, obj):
        return ('<a href="%(url)s" target="_blank">%(num)s</a>') % {
            'url': '/admin/dinghuo/orderdetail/?chichu_id=%s' % obj.sku_id,
            'num': obj.inbound_quantity
        }

    inbound_quantity_link.allow_tags = True
    inbound_quantity_link.short_description = u'入仓数'
    inbound_quantity_link.admin_order_field = 'inbound_quantity'

    def return_quantity_link(self, obj):
        return obj.return_quantity
        # return ('<a href="%(url)s" target="_blank">%(num)s</a>') % {
        #     'url': '/admin/dinghuo/orderdetail/?chichu_id=1&sku_id=%(sku)s',
        #     'sku': obj.sku_id,
        #     'num': obj.return_quantity
        # }

    # return_quantity_link.allow_tags = True
    return_quantity_link.short_description = u'用户退货数'
    return_quantity_link.admin_order_field = 'return_quantity'

    def rg_quantity_link(self, obj):
        return ('<a href="%(url)s" target="_blank">%(num)s</a>') % {
            'url': '/admin/dinghuo/returngoods/?rg_details__skuid=%s' % obj.sku_id,
            'num': obj.rg_quantity
        }

    rg_quantity_link.allow_tags = True
    rg_quantity_link.short_description = u'仓库退货数'
    rg_quantity_link.admin_order_field = 'rg_quantity'

    def product_title(self, obj):
        return self.PRODUCT_LINK % {
            'product_url': '/admin/items/product/%d/' % obj.sku.product.id,
            'product_title': obj.product.name
        }

    product_title.allow_tags = True
    product_title.short_description = u'商品名称'

    def now_quantity(self, obj):
        return obj.realtime_quantity

    now_quantity.short_description = u'实时库存'
    now_quantity.admin_order_field = 'now_quantity'

    def properties_name_alias(self, obj):
        return obj.sku.properties_name

    properties_name_alias.short_description = u'规格'

    def lookup_allowed(self, lookup, value):
        if lookup in ['product__name', 'product__outer_id']:
            return True
        return super(ProductSkuStatsAdmin, self).lookup_allowed(lookup, value)

    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        # self.history_quantity + self.inbound_quantity + self.return_quantity + self.adjust_num - self.rg_quantity
        orderingdict = {'now_quantity': (F('rg_quantity') - F('history_quantity')
                                         - F('inbound_quantity') - F('return_quantity') - F('adjust_num'),
                                         F('history_quantity') + F('inbound_quantity') +
                                         F('return_quantity') + F('adjust_num') - F('rg_quantity'))
                        }
        from django.contrib.admin.views.main import ChangeList, ORDER_VAR
        class StatsOrderChangeList(ChangeList):
            def get_ordering(self, request, queryset):
                params = self.params
                ordering = list(self.model_admin.get_ordering(request)
                                or self._get_default_ordering())
                if ORDER_VAR in params:
                    # Clear ordering and used params
                    ordering = []
                    order_params = params[ORDER_VAR].split('.')
                    for p in order_params:
                        try:
                            none, pfx, idx = p.rpartition('-')
                            field_name = self.list_display[int(idx)]
                            order_field = self.get_ordering_field(field_name)
                            if not order_field:
                                continue
                            if order_field in orderingdict:
                                if pfx == '-':
                                    ordering.append(orderingdict[order_field][0])
                                else:
                                    ordering.append(orderingdict[order_field][1])
                            elif order_field.startswith('-') and pfx == "-":
                                ordering.append(order_field[1:])
                            else:
                                ordering.append(pfx + order_field)
                        except (IndexError, ValueError):
                            continue
                ordering.extend(queryset.query.order_by)
                pk_name = self.lookup_opts.pk.name
                if not (set(ordering) & {'pk', '-pk', pk_name, '-' + pk_name}):
                    ordering.append('-pk')
                return ordering

        return StatsOrderChangeList


admin.site.register(InferiorSkuStats, InferiorSkuStatsAdmin)


class ProductSkuSaleStatsAdmin(admin.ModelAdmin):
    list_display = ('sku_id', 'properties_name', 'init_waitassign_num', 'num', 'sale_start_time', 'sale_end_time')
    search_fields = ['=sku_id']
    list_per_page = 25


admin.site.register(ProductSkuSaleStats, ProductSkuSaleStatsAdmin)


class ContrastContentAdmin(admin.ModelAdmin):
    list_display = ('cid', 'name', 'sid', 'status')


admin.site.register(ContrastContent, ContrastContentAdmin)


class ImageWaterMarkAdmin(admin.ModelAdmin):
    class Media:
        js = ('//cdn.bootcss.com/plupload/2.1.7/plupload.full.min.js',
              'script/qiniu.js', 'js/image_watermark.js')

    list_display = ('id', 'pic_preview', 'remark', 'status')

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': 60})}
    }
    actions = ['mark_invalid']

    PIC_PREVIEW_TPL = (
        '<a href="%(item_url)s" target="_blank">'
        '<img src="%(image_url)s" width="100px" height="100px"></a>')

    def pic_preview(self, obj):
        url = obj.url or '%s%s' % (settings.MEDIA_URL, settings.NO_PIC_PATH)
        return self.PIC_PREVIEW_TPL % {
            'item_url': '/admin/items/imagewatermark/%d/' % obj.id,
            'image_url': '%s?imageMogr2/thumbnail/100/format/jpg/quality/90' % url
        }

    pic_preview.allow_tags = True
    pic_preview.short_description = u'预览'

    def mark_invalid(self, request, queryset):
        queryset.update(status=0)

    mark_invalid.short_description = u'设为作废'


admin.site.register(ImageWaterMark, ImageWaterMarkAdmin)
