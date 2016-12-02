# -*- coding:utf-8 -*-
import time
from cStringIO import StringIO

from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.http import HttpResponse
from django.http import HttpResponseRedirect

from core.admin import BaseModelAdmin
from core.options import log_action, CHANGE
from core.utils import CSVUnicodeWriter
from flashsale.dinghuo import permissions as perms
from flashsale.dinghuo.filters import DateFieldListFilter
from flashsale.dinghuo.models import OrderList, OrderDetail, ProductSkuDetail, ReturnGoods, RGDetail, \
    UnReturnSku, LackGoodOrder, SupplyChainDataStats, SupplyChainStatsOrder, DailySupplyChainStatsOrder, \
    PayToPackStats, PackageBackOrderStats
from flashsale.dinghuo.models_user import MyUser, MyGroup
from shopback.trades.models import PackageSkuItem
from shopback.warehouse import WARE_THIRD
from .filters import OrderListStatusFilter2, BuyerNameFilter, \
    InBoundCreatorFilter
import datetime


class orderdetailInline(admin.TabularInline):
    model = OrderDetail
    fields = ('product_id', 'chichu_id', 'product_name', 'outer_id', 'product_chicun', 'buy_quantity', 'buy_unitprice',
              'total_price', 'arrival_quantity')
    extra = 3

    def get_readonly_fields(self, request, obj=None):
        if not perms.has_change_order_list_inline_permission(request.user):
            return self.readonly_fields + (
                'product_id', 'chichu_id', 'product_name', 'outer_id', 'product_chicun', 'buy_quantity',
                'arrival_quantity')
        return self.readonly_fields


class OrderListAdmin(BaseModelAdmin):
    fieldsets = ((u'订单信息:', {
        'classes': ('expand',),
        'fields': ('express_company', 'express_no', 'status', 'order_amount', 'note', 'p_district', 'stage',
                   'purchase_order_unikey')
    }),)
    inlines = [orderdetailInline]

    list_display = (
        'id', 'buyer_select', 'order_amount', 'calcu_model_num', 'quantity', 'purchase_total_num', 'shelf_status',
        'created', 'press_num', 'stage', 'get_receive_status', 'is_postpay', 'changedetail', 'supplier', 'note_name',
        'purchase_order_unikey_link', 'express_no', 'remind_link')
    list_filter = (('created', DateFieldListFilter), 'stage', 'arrival_process', 'is_postpay', 'press_num',
                   'pay_status', BuyerNameFilter, 'last_pay_date', 'created_by')
    search_fields = ['id', 'supplier__supplier_name', 'supplier_shop', 'express_no', 'note', 'purchase_order_unikey']
    date_hierarchy = 'created'

    list_per_page = 25

    class Media:
        css = {"all": ("css/admin_css.css", "https://cdn.bootcss.com/lightbox2/2.7.1/css/lightbox.css")}
        js = ("https://cdn.bootcss.com/lightbox2/2.7.1/js/lightbox.js",
              "layer-v1.9.2/layer/layer.js", "layer-v1.9.2/layer/extend/layer.ext.js", "js/admin_js.js",
              "js/dinghuo_orderlist.js")

    def queryset(self, request):
        qs = super(OrderListAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.exclude(status=u'作废')

    def buyer_select(self, obj):
        part = ['<select class="buyer-select" orderlist-id="%d" onchange="buyer_select(this)">' % obj.id]
        part.append('<option value="0">-------------</option>')

        for user in User.objects.filter(is_staff=True,
                                        groups__name__in=(u'小鹿买手资料员', u'小鹿采购管理员', u'小鹿采购员', u'管理员', u'小鹿管理员')). \
                distinct().order_by('id'):
            username = '%s%s' % (user.last_name, user.first_name)
            username = username or user.username
            if user.id == obj.buyer_id:
                part.append('<option value="%d" selected>%s</option>' % (user.id, username))
            else:
                part.append('<option value="%d">%s</option>' % (user.id, username))
        part.append('</select>')
        return ''.join(part)

    buyer_select.allow_tags = True
    buyer_select.short_description = u'负责人'

    def shelf_status(self, obj):
        if obj.status != OrderList.SUBMITTING:
            return ''
        details = obj.order_list.all()
        for detail in details:
            pro = Product.objects.get(id=detail.product_id)
            if pro.shelf_status:
                return ''
        return "已下架"

    shelf_status.short_description = u"是否下架"

    def calcu_item_sum_amount(self, obj):
        amount = 0
        details = obj.order_list.all()
        for detail in details:
            pro = Product.objects.get(id=detail.product_id)
            amount += detail.buy_quantity * pro.cost
        return amount

    calcu_item_sum_amount.allow_tags = True
    calcu_item_sum_amount.short_description = u"录入价"

    def calcu_model_num(self, obj):
        """计算显示款式数量"""
        dics = obj.order_list.all().values('outer_id').distinct()
        se = set()
        for i in dics:
            se.add(i['outer_id'][0:11]) if len(i['outer_id']) > 11 else se.add(i['outer_id'])
        return len(se)

    calcu_model_num.allow_tags = True
    calcu_model_num.short_description = u"款数"

    def quantity(self, obj):
        alldetails = OrderDetail.objects.filter(orderlist_id=obj.id, buy_quantity__gt=0)
        quantityofoneorder = 0
        for detail in alldetails:
            quantityofoneorder += detail.buy_quantity
        return '{0}'.format(quantityofoneorder)

    quantity.allow_tags = True
    quantity.short_description = u"商品数量"

    def get_receive_status(self, obj):
        return obj.get_receive_status()

    get_receive_status.short_description = u"到货状态"

    def supply_chain(self, obj):
        return u'<div style="width: 150px;overflow: hidden;white-space: nowrap;text-overflow: ellipsis;"><a href="{0}" target="_blank" >{1}</a></div>'.format(
            obj.supplier_name,
            obj.supplier_shop or obj.supplier_name)

    supply_chain.allow_tags = True
    supply_chain.short_description = u"供应商"

    def display_pic(self, obj):
        return u'<a href="#{0}" onclick="show_pic({0})" >图片{0}</a>'.format(obj.id)

    display_pic.allow_tags = True
    display_pic.short_description = u"显示图片"

    def note_name(self, obj):
        return u'<pre style="white-space: pre-wrap;word-break:break-all;width:100px;">{0}</pre>'.format(
            obj.note)

    note_name.allow_tags = True
    note_name.short_description = "备注"

    def shenhe(self, obj):
        symbol_link = obj.get_status_display()
        return symbol_link

    shenhe.allow_tags = True
    shenhe.short_description = u"状态"

    def purchase_order_unikey_link(self, obj):
        if obj.status == OrderList.SUBMITTING:
            return obj.purchase_order_unikey

        return u'<a href="/admin/trades/packageskuitem/?o=11.-10&q=%s" target="_blank" style="display: block;" >%s</a>' % (
            obj.purchase_order_unikey, obj.purchase_order_unikey)

    purchase_order_unikey_link.allow_tags = True
    purchase_order_unikey_link.short_description = "订单列表"

    def remind_link(self, obj):
        t = datetime.datetime.now() - datetime.timedelta(days=30)
        psi = PackageSkuItem.get_need_purchase({'pay_time__gt': t}).first()
        if psi:
            t1 = datetime.datetime.now() - psi.pay_time
            hours = int(t1.total_seconds() / 3600)
        else:
            hours = 0
        return u'<a href="/admin/trades/packageskuitem/?assign_status__exact=0&o=11.-10&purchase_order_unikey=" target="_blank" style="display: block;">%s小时前</a>' % hours

    remind_link.allow_tags = True
    remind_link.short_description = '未订货警告'

    def changedetail(self, obj):
        symbol_link = u'【详情页】'
        return u'<a href="/sale/dinghuo/changedetail/{0}/" target="_blank" style="display: block;" >{1}</a>'.format(
            int(obj.id), symbol_link)

    changedetail.allow_tags = True
    changedetail.short_description = "更改订单"

    def orderlist_ID(self, obj):
        symbol_link = obj.id or u'【空标题】'
        return '<a href="/sale/dinghuo/detail/{0}/" >{1}</a>'.format(int(obj.id), symbol_link)

    orderlist_ID.allow_tags = True
    orderlist_ID.short_description = "订单编号"

    def get_readonly_fields(self, request, obj=None):
        if not perms.has_change_order_list_inline_permission(request.user):
            return self.readonly_fields + ('status', 'supplier_shop',)
        return self.readonly_fields

    def get_actions(self, request):

        user = request.user
        actions = super(OrderListAdmin, self).get_actions(request)

        if user.is_superuser:
            return actions
        else:
            del actions["action_quick_complete"]
            return actions

    def get_changelist(self, request, **kwargs):
        return OrderListChangeList

    # 批量审核
    # def test_order_action(self, request, queryset):
    #     for p in queryset:
    #         pds = PurchaseDetail.objects.filter(purchase_order_unikey=orderlist.purchase_order_unikey)
    #         psis_total = 0
    #         for pd in pds:
    #             psi_res = PackageSkuItem.objects.filter(sku_id=pd.sku_id,assign_status=PackageSkuItem.NOT_ASSIGNED,purchase_order_unikey='').aggregate(total=Sum('num'))
    #             psi_total = psi_res['total'] or 0
    #             psis_total += psi_total
    #
    #         ods_res = OrderDetail.objects.filter(purchase_order_unikey=p.purchase_order_unikey).aggregate(total=Sum('buy_quantity'))
    #         ods_total = ods_res['total'] or 0
    #         if psis_total != ods_total:
    #             log_action(request.user.id, p, CHANGE, u'数量不对，审核失败')
    #             break
    #
    #         if p.status != "审核":
    #             p.set_stage_verify()
    #             log_action(request.user.id, p, CHANGE, u'审核订货单')
    #
    #             self.message_user(request, u"已成功审核!")
    #
    #     return HttpResponseRedirect(request.get_full_path())
    #
    # test_order_action.short_description = u"审核(已付款)"

    def verify_order_action(self, request, queryset):
        print 'verify_order_action', request
        for orderlist in queryset:
            sku_ids = list(orderlist.purchase_order.arrangements.values_list('sku_id', flat=True))
            psis = PackageSkuItem.get_need_purchase({'sku_id__in': sku_ids})
            psis_total = psis.aggregate(total=Sum('num')).get('total') or 0
            ods_res = OrderDetail.objects.filter(purchase_order_unikey=orderlist.purchase_order_unikey).aggregate(
                total=Sum('buy_quantity'))
            ods_total = ods_res['total'] or 0
            if psis_total == 0:
                log_action(request.user.id, orderlist, CHANGE, u'至少要有一个待订货skuitem')
                break
            if psis_total != ods_total:
                log_action(request.user.id, orderlist, CHANGE, u'数量不对，审核失败')
                break
            if orderlist.supplier.ware_by == WARE_THIRD and orderlist.stage < OrderList.STAGE_CHECKED:
                from flashsale.finance.models import Bill
                psi_oids = [p.oid for p in psis]
                orderlist.begin_third_package(psi_oids)
                Bill.create([orderlist], Bill.PAY, Bill.STATUS_DELAY, Bill.TRANSFER_PAY, 0, 0, orderlist.supplier,
                            user_id=request.user.id, receive_account='', receive_name='',
                            pay_taobao_link='', transcation_no='')
                self.message_user(request, str(orderlist.id) + u'订货单已成功进入结算!')
            elif orderlist.stage < OrderList.STAGE_CHECKED:
                orderlist.set_stage_verify()
                log_action(request.user.id, orderlist, CHANGE, u'审核订货单')
                self.message_user(request, u'已成功审核!')
        return HttpResponseRedirect(request.get_full_path())

    verify_order_action.short_description = u'审核(待支付)'

    # 批量验货完成
    def action_quick_complete(self, request, queryset):
        count = 0
        for p in queryset:
            if p.status == OrderList.APPROVAL:
                p.status = OrderList.DEALED
                p.save()
                log_action(request.user.id, p, CHANGE, u'过期处理订货单')
                count += 1
        self.message_user(request, u"成功处理{0}个订货单!".format(str(count)))

        return HttpResponseRedirect(request.get_full_path())

    action_quick_complete.short_description = u"处理过期订货单（批量 ）"

    def action_receive_money(self, request, queryset):
        for order in queryset:
            if order.pay_status != u'正常':
                order.pay_status = u'正常'
                order.save()
                log_action(request.user.id, order, CHANGE, u'已收款')
        return HttpResponseRedirect(request.get_full_path())

    action_receive_money.short_description = u'收款（批量）'

    def export_orderlist_action(self, request, queryset):
        """ 导出订货单信息 """

        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') > -1
        dump_fields = [('id', u'订货单ID'), ('supplier__supplier_name', u'供应商'),
                       ('buyer__username', u'采购员'),
                       ('purchase_total_num', u'订货数量'), ('order_amount', u'订货金额'),
                       ('created', u'创建时间'), ('paid_time', u'付款日期'),
                       ('receive_time', u'收货日期'), ('stage', u'状态')]
        orderlist_csvdata = []
        orderlist_csvdata.append([f[1] for f in dump_fields])
        orderlist_values = queryset.values_list(*[d[0] for d in dump_fields])
        for order in orderlist_values:
            orderlist_csvdata.append(('%s' % v for v in order))
        tmpfile = StringIO()
        writer = CSVUnicodeWriter(tmpfile, encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(orderlist_csvdata)
        response = HttpResponse(tmpfile.getvalue(), content_type='application/octet-stream')
        tmpfile.close()
        response['Content-Disposition'] = 'attachment; filename=orderlist-%s.csv' % str(int(time.time()))
        return response

    export_orderlist_action.short_description = u'订货单信息导出'

    actions = ['verify_order_action', 'action_quick_complete', 'action_receive_money', 'export_orderlist_action']


class OrderListChangeList(ChangeList):
    def get_queryset(self, request):
        qs = self.root_queryset
        search_q = request.GET.get('q', '').strip()
        if search_q.isdigit():
            trades = qs.filter(id=search_q)
            return trades
        return super(OrderListChangeList, self).get_queryset(request)


class orderdetailAdmin(BaseModelAdmin):
    fieldsets = ((u'订单信息:', {
        'classes': ('expand',),
        'fields': (
            'product_id', 'outer_id', 'product_name', 'chichu_id', 'product_chicun', 'buy_quantity', 'arrival_quantity',
            'inferior_quantity', 'non_arrival_quantity', 'purchase_detail_unikey', 'purchase_order_unikey')
    }),)

    list_display = (
        'id','link_order', 'orderlist_status', 'product_id', 'outer_id', 'product_name', 'chichu_id', 'product_chicun',
        'buy_quantity',
        'arrival_quantity', 'inferior_quantity', 'non_arrival_quantity', 'created', 'updated', 'purchase_order_unikey',
        'purchase_detail_unikey','buyer'
    )
    list_filter = (('created', DateFieldListFilter), OrderListStatusFilter2)
    search_fields = ['id', 'orderlist__id', 'product_id', 'outer_id', 'chichu_id', 'purchase_order_unikey',
                     'purchase_detail_unikey','product_name']
    date_hierarchy = 'created'

    def link_order(self, obj):
        order_list = obj.orderlist
        if order_list:
            link_str = u"<a href='/sale/dinghuo/changedetail/{0}/' target='_blank'>{1}</a>".format(order_list.id,
                                                                                                   obj.orderlist.__unicode__())
        else:
            link_str = u"<a href='#' target='_blank'>None</a>"
        return link_str

    link_order.allow_tags = True
    link_order.short_description = u"订货单"

    def orderlist_status(self, obj):
        order_list = obj.orderlist
        return order_list.get_stage_display()

    orderlist_status.short_description = u"订货状态"

    def buyer(self, obj):
        return obj.orderlist.buyer

    def queryset(self, request):
        qs = super(orderdetailAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.exclude(orderlist__status='作废')


admin.site.register(OrderList, OrderListAdmin)
admin.site.register(OrderDetail, orderdetailAdmin)

from django.contrib.auth.models import User


class myuserAdmin(BaseModelAdmin):
    fieldsets = ((u'用户信息:', {
        'classes': ('expand',),
        'fields': ('user', 'group')
    }),)

    list_display = (
        'user', 'group'
    )
    list_filter = ('group',)
    search_fields = ['user__username']

    def get_form(self, request, obj=None, **kwargs):
        form = super(myuserAdmin, self).get_form(request, obj=obj, **kwargs)

        form.base_fields['user'].queryset = form.base_fields['user'].queryset \
            .filter(is_staff=True)

        return form


admin.site.register(MyUser, myuserAdmin)
admin.site.register(MyGroup)


class PayToPackStatsAdmin(admin.ModelAdmin):
    list_display = ('pay_date', 'packed_sku_num', 'total_days', 'avg_post_days', 'updated')


admin.site.register(PayToPackStats, PayToPackStatsAdmin)


class SupplyChainDataStatsAdmin(BaseModelAdmin):
    list_display = ('sale_quantity', 'cost_amount', 'turnover',
                    'order_goods_quantity', 'order_goods_amount',
                    'stats_time', 'group',
                    'created', 'updated')
    list_filter = ('group', 'created',)
    search_fields = ['group']
    ordering = ('-stats_time',)


admin.site.register(SupplyChainDataStats, SupplyChainDataStatsAdmin)
from flashsale.dinghuo.models import DailyStatsPreview


class DailyStatsPreviewAdmin(admin.ModelAdmin):
    list_display = ('sale_time', 'shelf_num', 'sale_num', "time_to_day",
                    'return_num', 'cost_of_product', 'sale_money', 'return_money')
    list_filter = ('created',)


admin.site.register(DailyStatsPreview, DailyStatsPreviewAdmin)


class SupplyChainStatsOrderAdmin(BaseModelAdmin):
    list_display = ('product_id', 'outer_sku_id', 'sale_time', 'shelve_time', 'sale_num', 'trade_general_time_name',
                    'ding_huo_num', 'order_deal_time_name',
                    'arrival_num', 'goods_arrival_time_name',
                    'goods_out_num', 'goods_out_time_name', "refund_amount_num", "refund_num")
    search_fields = ['product_id']

    def trade_general_time_name(self, obj):
        temp_data = obj.trade_general_time
        return time.strftime('%Y-%m-%d %H:%m', time.localtime(temp_data)) if temp_data > 0 else 0

    trade_general_time_name.allow_tags = True
    trade_general_time_name.short_description = "订单生成"

    def order_deal_time_name(self, obj):
        temp_data = obj.order_deal_time
        return time.strftime('%Y-%m-%d %H:%m', time.localtime(temp_data)) if temp_data > 0 else 0

    order_deal_time_name.allow_tags = True
    order_deal_time_name.short_description = "订货时间"

    def goods_arrival_time_name(self, obj):
        temp_data = obj.goods_arrival_time
        return time.strftime('%Y-%m-%d %H:%m', time.localtime(temp_data)) if temp_data > 0 else 0

    goods_arrival_time_name.allow_tags = True
    goods_arrival_time_name.short_description = "到货时间"

    def goods_out_time_name(self, obj):
        temp_data = obj.goods_out_time
        return time.strftime('%Y-%m-%d %H:%m', time.localtime(temp_data)) if temp_data > 0 else 0

    goods_out_time_name.allow_tags = True
    goods_out_time_name.short_description = "出货时间"


admin.site.register(SupplyChainStatsOrder, SupplyChainStatsOrderAdmin)


class DailySupplyChainStatsOrderAdmin(admin.ModelAdmin):
    list_display = (
        'product_id', 'sale_time', 'trade_general_time', 'order_deal_time', 'goods_arrival_time', 'goods_out_time',
        'ding_huo_num', 'fahuo_num', 'sale_num', 'cost_of_product', 'sale_cost_of_product', 'return_num', 'return_pro',
        'inferior_num')
    search_fields = ['product_id']


admin.site.register(DailySupplyChainStatsOrder, DailySupplyChainStatsOrderAdmin)


class ProductSkuDetailAdmin(admin.ModelAdmin):
    list_display = (
        'product_sku', 'exist_stock_num', 'created')


admin.site.register(ProductSkuDetail, ProductSkuDetailAdmin)
from flashsale.dinghuo.models import RecordGroupPoint


class RecordGroupPointAdmin(admin.ModelAdmin):
    list_display = (
        'group_name', 'point_type', 'point_content', 'get_point', 'record_time')
    search_fields = ['point_content']
    list_filter = ['group_name', ('record_time', DateFieldListFilter), 'point_type']

    def queryset(self, request):
        qs = super(RecordGroupPointAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.exclude(get_point='0')


admin.site.register(RecordGroupPoint, RecordGroupPointAdmin)


class RGDetailInline(admin.TabularInline):
    model = RGDetail
    fields = ("skuid", "return_goods", "num", "inferior_num", "price")


from shopback.items.models import Product
from flashsale.pay.models import SaleRefund


class ReturnGoodsAdmin(BaseModelAdmin):
    list_display = ('id_link', "supplier_link", "show_detail_num", "sum_amount", "type",
                    "status", "status_contrl", "noter", "transactor_name", "created",
                    "consign_time", "sid", "consigner", 'show_memo', 'show_reason'
                    )
    search_fields = ['id', "supplier__id", "supplier__supplier_name", "transaction_number",
                     "noter", "consigner", "transactor_id", "sid"]

    list_filter = ["type", "status", "noter", "consigner", "transactor_id",
                   ("created", DateFieldListFilter), ("modify", DateFieldListFilter)]
    readonly_fields = ('status', "type", 'supplier')
    inlines = [RGDetailInline, ]
    list_display_links = []
    list_select_related = True
    list_per_page = 25

    # change_form_template = "admin/dinghuo/returngoods/change_form.html"
    def lookup_allowed(self, lookup, value):
        if lookup in ['supplier__supplier_name']:
            return True
        return super(ReturnGoodsAdmin, self).lookup_allowed(lookup, value)

    def id_link(self, obj):
        return ('<a href="%(url)s" target="_blank">'
                '%(show_text)s</a>') % {
                   'url': '/admin/dinghuo/returngoods/%d/' % obj.id,
                   'show_text': str(obj.id)
               }

    id_link.allow_tags = True
    id_link.short_description = u"ID"

    def detail_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = {'title': u'仓库退货单', 'transactors': ReturnGoods.transactors()}
        return self.detailform_view(request, object_id, form_url, extra_context)

    # def change_view(self, request, object_id, form_url='', extra_context=None):
    #     extra_context = {'title': u'仓库退货单', 'transactors': ReturnGoods.transactors()}
    #     return self.changeform_view(request, object_id, form_url, extra_context)

    def transactor_name(self, obj):
        return obj.transactor.username

    transactor_name.short_description = u"负责人"

    def supplier_link(self, obj):
        if not obj.supplier:
            return ''

        return ('<a href="%(url)s" target="_blank">'
                '%(show_text)s</a> 《') % {
                   'url': '/admin/supplier/salesupplier/%d/' % obj.supplier_id,
                   'show_text': obj.supplier.supplier_name
               } + ('<a href="%(url)s">'
                    '%(show_text)s</a>》 ') % {
                       'url': '/admin/dinghuo/returngoods?supplier_id=%d' % obj.supplier_id,
                       'show_text': obj.supplier.id
                   }

    supplier_link.allow_tags = True
    supplier_link.short_description = u"供应商"

    def product_desc(self, obj):
        return '<br/>'.join([p.title() for p in obj.products])

    # def show_pic(self, obj):
    #     product_id = obj.product_id
    #     pro = Product.objects.get(id=product_id)
    #     try:
    #         suplier = SaleSupplier.objects.get(id=obj.supplier_id)
    #         supplier_name = suplier.supplier_name
    #         mobile = suplier.mobile
    #         address = suplier.address
    #     except SaleSupplier.DoesNotExist:
    #         supplier_name = u"none"
    #         mobile = u"none"
    #         address = u"none"
    #     js_str = u"'%s','%s','%s'" % (
    #         supplier_name or u"none", mobile or u"none", address or u"none")
    #     html = u'<img src="{0}" style="width:62px;height:100px"><a style="display:inline" onclick="supplier_admin({4})">供应商：{3}</a>' \
    #            u'<br><a target="_blank" href="/admin/items/product/?id={2}">{1}</a>'.format(pro.pic_path, pro.name,
    #                                                                                         product_id,
    #                                                                                         obj.supplier_id, js_str)
    #     return html

    product_desc.allow_tags = True
    product_desc.short_description = u"包含商品"

    def show_reason(self, obj):
        html = u''
        refs = SaleRefund.objects.filter(item_id=obj.product_id, good_status__in=(SaleRefund.BUYER_RECEIVED,
                                                                                  SaleRefund.BUYER_RETURNED_GOODS))
        if refs.count() >= 10:  # 最多显示10 个退货描述
            refs = refs[:10]
        for ref in refs:
            html += u'<br>' + ref.desc
        return html

    show_reason.allow_tags = True
    show_reason.short_description = u"原因"

    def show_detail_num(self, obj):
        return_num = 0
        dts = obj.rg_details.all()
        html = ''
        for dt in dts:
            skuid = dt.skuid
            num = dt.num
            return_num = return_num + num
            price = dt.price
            # sub_html = u'{0}  {1} - {2}<br>'.format(skuid, return_num, price)
            # html = html + sub_html
        html = u'{0}<br>'.format(return_num)
        return html

    show_detail_num.allow_tags = True
    show_detail_num.short_description = u"退货数量"

    # def deal_sum_amount(self, obj):
    #     html = u'<a onclick="change_sum_price({0},{2})">{1}</a>'.format(obj.id, obj.sum_amount, obj.return_num)
    #     return html
    #
    # deal_sum_amount.allow_tags = True
    # deal_sum_amount.short_description = u"退款总额"

    def status_contrl(self, obj):
        if obj.status == ReturnGoods.CREATE_RG:
            # 如果是创建状态则　显示　审核通过　作废退货　两个按钮
            html = u'<a cid="{0}" onclick="verify_ok(this)" style="margin-right:0px;">审核通过</a><br/>' \
                   u'<a cid="{0}" onclick="verify_no(this)">作废退货</a>'.format(obj.id, )
            return html
        elif obj.status == ReturnGoods.DELIVER_RG:
            # 如果是已经发货　　显示　退货成功　退货失败　两个按钮
            html = u'<a cid="{0}" onclick="send_ok(this)" style="margin-right:0px;">退货成功</a><br/>' \
                   u'<a cid="{0}" onclick="send_fail(this)">退货失败</a>'.format(obj.id, )
            return html
        else:
            return obj.get_status_display()

    status_contrl.allow_tags = True
    status_contrl.short_description = u"操作"

    def show_memo(self, obj):
        memo = u'{0}'.format(str(obj.memo).replace('\r', '<br><br>'))
        return memo

    show_memo.allow_tags = True
    show_memo.short_description = u"备注信息"

    def lookup_allowed(self, lookup, value):
        if lookup in ['rg_details__skuid']:
            return True
        return super(ReturnGoodsAdmin, self).lookup_allowed(lookup, value)

    class Meta:
        # related_fkey_lookups = ['rg_details__skuid']
        css = {"all": (
            "css/admin_css.css", "css/return_goods.css", "https://cdn.bootcss.com/lightbox2/2.7.1/css/lightbox.css",
        )}
        js = ("js/tuihuo_ctrl.js", "https://cdn.bootcss.com/lightbox2/2.7.1/js/lightbox.js",
              "layer-v1.9.2/layer/layer.js", "layer-v1.9.2/layer/extend/layer.ext.js")


admin.site.register(ReturnGoods, ReturnGoodsAdmin)


class UnReturnSkuAdmin(BaseModelAdmin):
    list_display = (
        'id', 'product_outer_id', "product_name", "sku_properties_name", "supplier_sku", "supplier_name", "reason",
        "creater_name", "created", "modified", "status")
    search_fields = ['^product__name', "=supplier__id", "^supplier__supplier_name", "=product__id", "=sku__id"]
    list_filter = ["status", "reason"]
    readonly_fields = ('product', 'sale_product', 'sku', 'supplier', 'creater')
    # inlines = [RGDetailInline, ]
    # list_display_links = ['id',]
    # list_select_related = True
    list_per_page = 50

    def product_outer_id(self, obj):
        return '<a href="/admin/items/product/?outer_id=%(outer_id)s">%(outer_id)s</a>' % {
            'outer_id': obj.product.outer_id}

    product_outer_id.short_description = '商品编码'
    product_outer_id.allow_tags = True

    def product_name(self, obj):
        return obj.product.name;

    product_name.short_description = '商品名称'

    def sku_properties_name(self, obj):
        if obj.sku:
            return '<a href="/admin/items/skustock/?sku_id=%(sku_id)d">%(properties_name)s</a>' % {
                'sku_id': obj.sku.id,
                'properties_name': obj.sku.properties_name or obj.sku.properties_alias or ''
            }
        else:
            return ''

    sku_properties_name.allow_tags = True
    sku_properties_name.short_description = '规格'

    def supplier_sku(self, obj):
        return obj.sale_product.supplier_sku

    supplier_sku.short_description = '货号'

    def supplier_name(self, obj):
        return obj.supplier.supplier_name

    supplier_name.short_description = '供应商名称'

    def creater_name(self, obj):
        user = obj.creater
        last_name = user.last_name
        first_name = user.first_name
        if len(last_name) > 1:
            names = [first_name, last_name]
        else:
            names = [last_name, first_name]
        return ''.join(filter(None, names)) or user.username

    creater_name.short_description = '创建人'

    def lookup_allowed(self, lookup, value):
        if lookup in ['product___name', 'sale_product__name', 'supplier__supplier_name', 'sku__id']:
            return True
        return super(UnReturnSkuAdmin, self).lookup_allowed(lookup, value)


admin.site.register(UnReturnSku, UnReturnSkuAdmin)

from .models import SaleInventoryStat


class SaleInventoryStatAdmin(admin.ModelAdmin):
    list_display = ('stat_date', 'newly_increased', 'not_arrive', 'arrived', 'deliver', 'inventory')
    list_filter = ('category',)


admin.site.register(SaleInventoryStat, SaleInventoryStatAdmin)

from .models import InBound, InBoundDetail, OrderDetailInBoundDetail


class InBoundAdmin(BaseModelAdmin):
    fieldsets = ((
                     u'详情', {
                         'classes': ('expand',),
                         'fields': ('express_no', 'sent_from', 'memo', 'forecast_inbound_id')
                     }
                 ),)

    list_display = ('id', 'show_id', 'show_creator', 'supplier', 'express_no',
                    'show_orderlists', 'created', 'status', 'show_status_info', 'memo')

    list_filter = ('status', 'created', 'checked', 'wrong', 'out_stock', InBoundCreatorFilter)

    search_fields = ('=id', '=ori_orderlist_id', '=supplier__id', '=supplier__supplier_name', '=express_no')
    list_per_page = 20

    def show_creator(self, obj):
        from common.utils import get_admin_name
        return get_admin_name(obj.creator)

    show_creator.short_description = u'创建人'

    def show_id(self, obj):
        return '<a href="/sale/dinghuo/inbound/%(id)d" target="_blank">详情</a>' % {'id': obj.id}

    show_id.allow_tags = True
    show_id.short_description = u'详情'

    def show_orderlists(self, obj):
        tmp = []
        for orderlist_id in sorted(obj.orderlist_ids):
            tmp.append(
                '<a href="/sale/dinghuo/changedetail/%(id)d/" target="_blank">%(id)d</a>' % {'id': int(orderlist_id)})
        return ','.join(tmp)

    show_orderlists.allow_tags = True
    show_orderlists.short_description = u'关联订货单'

    def show_status_info(self, obj):
        return obj.get_set_status_info()

    show_status_info.allow_tags = True
    show_status_info.short_description = u'当前状态'


class InBoundDetailAdmin(admin.ModelAdmin):
    fieldsets = ((
                     u'详情', {
                         'classes': ('expand',),
                         'fields': (
                             'product_name', 'properties_name', 'arrival_quantity', 'inferior_quantity', 'status')
                     }
                 ),)
    list_display = (
        'id', 'show_inbound', 'product', 'sku', 'product_name', 'properties_name', 'arrival_quantity',
        'inferior_quantity',
        'created', 'modified', 'status')

    def show_inbound(self, obj):
        return '<a href="/sale/dinghuo/inbound/%(id)d" target="_blank">%(id)d</a>' % {
            'id': obj.inbound_id}

    show_inbound.allow_tags = True
    show_inbound.short_description = u'入仓单ID'


class OrderDetailInBoundDetailAdmin(admin.ModelAdmin):
    list_display = (
        'orderlist_id_link', 'show_orderdetail', 'inbound_id_link', 'show_inbounddetail', 'arrival_quantity',
        'inferior_quantity', 'created', 'status')

    def orderlist_id_link(self, obj):
        return '<a href="/sale/dinghuo/changedetail/%(id)d" target="_blank">%(id)d</a>' % {
            'id': obj.orderdetail.orderlist_id}

    orderlist_id_link.allow_tags = True
    orderlist_id_link.short_description = u'订货单ID'

    def inbound_id_link(self, obj):
        return '<a href="/sale/dinghuo/inbound/%(id)d" target="_blank">%(id)d</a>' % {
            'id': obj.inbounddetail.inbound_id}

    inbound_id_link.allow_tags = True
    inbound_id_link.short_description = u'入库单ID'

    def show_orderdetail(self, obj):
        return '<a href="/admin/dinghuo/orderdetail/?id=%(id)d" target="_blank">%(id)d</a>' % {'id': obj.orderdetail_id}

    show_orderdetail.allow_tags = True
    show_orderdetail.short_description = u'订货明细ID'

    def show_inbounddetail(self, obj):
        return '<a href="/admin/dinghuo/inbounddetail/?id=%(id)d" target="_blank">%(id)d</a>' % {
            'id': obj.inbounddetail_id}

    show_inbounddetail.allow_tags = True
    show_inbounddetail.short_description = u'入仓明细ID'

    def lookup_allowed(self, lookup, value):
        if lookup in ['inbounddetail__sku_id']:
            return True
        return super(OrderDetailInBoundDetailAdmin, self).lookup_allowed(lookup, value)


admin.site.register(InBound, InBoundAdmin)
admin.site.register(InBoundDetail, InBoundDetailAdmin)
admin.site.register(OrderDetailInBoundDetail, OrderDetailInBoundDetailAdmin)

from flashsale.dinghuo.models_purchase import PurchaseArrangement, PurchaseDetail, PurchaseOrder


class PurchaseArrangementAdmin(BaseModelAdmin):
    list_display = (
        'id', 'package_sku_item_id', 'oid', 'purchase_order_unikey', 'outer_id', 'outer_sku_id', 'sku_id', 'title',
        'sku_properties_name', 'num', 'status', 'purchase_order_status', 'initial_book', 'modified', 'created')
    list_filter = ('status', 'purchase_order_status')
    search_fields = ('=package_sku_item_id', '=oid', '=outer_id', '=title', '=sku_id', '=purchase_order_unikey')


admin.site.register(PurchaseArrangement, PurchaseArrangementAdmin)


class PurchaseDetailAdmin(BaseModelAdmin):
    list_display = (
        'id', 'outer_id', 'purchase_order_unikey', 'outer_sku_id', 'sku_id', 'title', 'sku_properties_name', 'book_num',
        'need_num', 'status', 'unit_price_display', 'modified', 'created')
    list_filter = ('status',)
    search_fields = ('=outer_id', '^title', '=sku_id', '=purchase_order_unikey')


admin.site.register(PurchaseDetail, PurchaseDetailAdmin)


class PurchaseOrderAdmin(BaseModelAdmin):
    list_display = ('id', 'uni_key', 'supplier_id', 'supplier_name', 'book_num', 'need_num', 'arrival_num', 'status',
                    'modified', 'created')
    list_filter = ('status',)
    search_fields = ('=supplier_id', '=supplier_name', '=uni_key')


admin.site.register(PurchaseOrder, PurchaseOrderAdmin)


class LackGoodOrderAdmin(BaseModelAdmin):
    list_display = ('id', 'supplier', 'product_id', 'sku_id', 'lack_num', 'refund_num', 'is_refund',
                    'refund_time', 'order_group_key', 'status', 'created')
    search_fields = ('=product_id', '=sku_id', 'order_group_key')

    actions = ['action_refund_manage', ]

    def get_form(self, request, obj=None, **kwargs):
        form = super(LackGoodOrderAdmin, self).get_form(request, obj=obj, **kwargs)
        if obj and obj.supplier:
            form.base_fields['supplier'].queryset = form.base_fields['supplier'].queryset.filter(
                id=obj.supplier.id)
        else:
            form.base_fields['supplier'].queryset = form.base_fields['supplier'].queryset.none()
        return form

    def action_refund_manage(self, request, queryset):
        first_obj = queryset.first()
        order_group_key = first_obj.order_group_key
        exclude_qs = queryset.exclude(order_group_key=order_group_key)
        if exclude_qs.exists():
            self.message_user(request,
                              u'请选择同一组键对应的缺货单,当前组键:[%s]' % ','.join(set([o.order_group_key for o in queryset])))
            return HttpResponseRedirect(request.get_full_path())

        return HttpResponseRedirect(reverse('dinghuo_v1:lackgoodorder-refund-manage', args=[order_group_key]) + '.html')

    action_refund_manage.short_description = u"缺货商品退款管理"

    def delete_model(self, request, obj):
        obj.status = obj.DELETE
        obj.save()


admin.site.register(LackGoodOrder, LackGoodOrderAdmin)


class PackageBackOrderStatsAdmin(BaseModelAdmin):
    list_display = (
        'id', 'day_date', 'purchaser', 'three_backorder_num', 'five_backorder_num', 'fifteen_backorder_num', 'created')
    search_fields = ('=id', '^purchaser__username')
    list_filter = [("created", DateFieldListFilter)]

    def get_form(self, request, obj=None, **kwargs):
        form = super(PackageBackOrderStatsAdmin, self).get_form(request, obj=obj, **kwargs)
        form.base_fields['purchaser'].queryset = form.base_fields['purchaser'].queryset.filter(
            id=obj and obj.purchaser and obj.purchaser.id)
        return form


admin.site.register(PackageBackOrderStats, PackageBackOrderStatsAdmin)
