# -*- coding:utf8 -*-
import datetime
import cStringIO as StringIO
from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
from shopback.users.models import User, Customer
from core.filters import DateFieldListFilter
from shopback import paramconfig as pcfg
from shopback.users import permissions as perms
from common.utils import gen_cvs_tuple, CSVUnicodeWriter


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'has_fenxiao', 'visitor_id', 'uid', 'nick', 'user_code'
                    , 'sync_stock', 'percentage', 'is_primary', 'created_at', 'status')
    list_display_links = ('id', 'nick')

    list_filter = ('status',)
    search_fields = ['id', 'nick']

    # --------设置页面布局----------------
    fieldsets = (('用户基本信息:', {
                    'classes': ('expand',),
                    'fields': (('user', 'visitor_id', 'uid')
                               , ('type', 'nick')
                               , ('user_code', 'contacter', 'phone')
                               , ('mobile', 'area_code', 'location'))
                }),
                 ('淘宝用户设置:', {
                     'classes': ('collapse',),
                     'fields': (('buyer_credit', 'seller_credit')
                                , ('has_fenxiao', 'auto_repost')
                                , ('item_img_num', 'item_img_size', 'prop_img_num', 'prop_img_size')
                                , ('alipay_bind', 'alipay_no'))
                 }),
                 ('高级设置:', {
                     'classes': ('expand',),
                     'fields': (('sync_stock', 'percentage', 'is_primary', 'status'),)
                 }))

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + ('user',)

    def get_actions(self, request):

        user = request.user
        actions = super(UserAdmin, self).get_actions(request)

        if not perms.has_delete_user_permission(user) and 'delete_selected' in actions:
            del actions['delete_selected']
        if not perms.has_download_orderinfo_permission(user) and 'pull_user_unpost_trades' in actions:
            del actions['pull_user_unpost_trades']
        if not perms.has_download_iteminfo_permission(user) and 'pull_user_items' in actions:
            del actions['pull_user_items']
        if not perms.has_manage_itemlist_permission(user) and 'autolist_user_items' in actions:
            del actions['autolist_user_items']
        if not perms.has_recover_instock_permission(user) and 'sync_online_prodnum_to_offline' in actions:
            del actions['sync_online_prodnum_to_offline']
        if not perms.has_async_threemtrade_permission(user) and 'async_pull_lastest_trades' in actions:
            del actions['async_pull_lastest_trades']
        return actions

    # 更新用户待发货订单
    def pull_user_unpost_trades(self, request, queryset):

        from shopback.orders.tasks import saveUserDuringOrdersTask
        from shopback.fenxiao.tasks import saveUserPurchaseOrderTask
        from shopapp.jingdong.tasks import pullJDOrderByVenderIdTask
        from shopapp.weixin.tasks import pullWaitPostWXOrderTask
        from shopapp.weixin.models import WXOrder

        pull_users = []
        for user in queryset:

            pull_dict = {'uid': user.visitor_id, 'nick': user.nick}
            try:
                if user.type in (User.SHOP_TYPE_B, User.SHOP_TYPE_C):
                    # 更新等待发货商城订单
                    saveUserDuringOrdersTask.delay(user.visitor_id, status=pcfg.WAIT_SELLER_SEND_GOODS)

                    # 更新待发货分销订单
                    saveUserPurchaseOrderTask.delay(user.visitor_id, status=pcfg.WAIT_SELLER_SEND_GOODS)
                elif user.type == User.SHOP_TYPE_JD:

                    pullJDOrderByVenderIdTask.delay(user.visitor_id)

                elif user.type == User.SHOP_TYPE_WX:

                    pullWaitPostWXOrderTask.delay(None, None, full_update=True)

            except Exception, exc:
                pull_dict['success'] = False
                pull_dict['errmsg'] = exc.message or '%s' % exc

            else:
                pull_dict['success'] = True
            pull_users.append(pull_dict)

        return render_to_response('users/pull_wait_post_trade.html',
                                  {'users': pull_users},
                                  context_instance=RequestContext(request),
                                  content_type="text/html")

    pull_user_unpost_trades.short_description = "下载待发货订单".decode('utf8')

    # 更新用户线上商品入库
    def pull_user_items(self, request, queryset):

        pull_users = []
        for user in queryset:
            pull_dict = {'uid': user.visitor_id, 'nick': user.nick}
            try:
                if user.type in (User.SHOP_TYPE_B, User.SHOP_TYPE_C):
                    # 更新等待发货商城订单
                    # 下载更新用户商品分销商品
                    from shopback.items.tasks import updateUserItemSkuFenxiaoProductTask
                    updateUserItemSkuFenxiaoProductTask.delay(user.visitor_id)

                elif user.type == User.SHOP_TYPE_JD:

                    from shopapp.jingdong.tasks import pullJDProductByVenderidTask
                    pullJDProductByVenderidTask.delay(user.visitor_id)

                elif user.type == User.SHOP_TYPE_WX:

                    from shopapp.weixin.tasks import pullWXProductTask
                    pullWXProductTask.delay()

            except Exception, exc:
                pull_dict['success'] = False
                pull_dict['errmsg'] = exc.message or '%s' % exc

            else:
                pull_dict['success'] = True
            pull_users.append(pull_dict)

        return render_to_response('users/pull_online_items.html', {'users': pull_users},
                                  context_instance=RequestContext(request), content_type="text/html")

    pull_user_items.short_description = "下载线上商品信息".decode('utf8')

    # 商品上下架
    def autolist_user_items(self, request, queryset):

        if queryset.count() != 1:
            return

        user = queryset[0]

        return HttpResponseRedirect(reverse('pull_from_taobao') + '?user_id=' + str(user.user.id))

    autolist_user_items.short_description = "管理商品上架时间".decode('utf8')

    # 线上库存覆盖系统库存
    def sync_online_prodnum_to_offline(self, request, queryset):

        if queryset.count() != 1:
            ret_params = {'success': False, 'errmsg': '请选择一个主店'}
        user = queryset[0]

        try:
            from shopback.items.tasks import updateUserProductSkuTask

            updateUserProductSkuTask(user.visitor_id, force_update_num=True)
        except Exception, exc:
            ret_params = {'success': False, 'errmsg': exc.message}
        else:
            ret_params = {'success': True}
        return render_to_response('users/sync_online_prodnum_template.html', ret_params,
                                  context_instance=RequestContext(request), content_type="text/html")

    sync_online_prodnum_to_offline.short_description = "线上库存覆盖系统库存".decode('utf8')

    # 异步下载近三个月订单
    def async_pull_lastest_trades(self, request, queryset):

        from shopapp.asynctask.tasks import task_async_order

        pull_users = []
        for user in queryset:
            pull_dict = {'uid': user.visitor_id, 'nick': user.nick}
            try:
                end_dt = datetime.datetime.now() - datetime.timedelta(1, 0, 0)
                for i in range(3):
                    s_dt = end_dt - datetime.timedelta((i + 1) * 30, 0, 0)
                    e_dt = end_dt - datetime.timedelta(i * 30, 0, 0)
                    # 异步批量更新订单
                    task_async_order.delay(s_dt, e_dt, user.visitor_id)
            except Exception, exc:
                pull_dict['success'] = False
                pull_dict['errmsg'] = exc.message or '%s' % exc
            else:
                pull_dict['success'] = True
            pull_users.append(pull_dict)

        return render_to_response('users/async_lastest_trades.html', {'users': pull_users},
                                  context_instance=RequestContext(request), content_type="text/html")

    async_pull_lastest_trades.short_description = "异步下载近三个月订单".decode('utf8')

    actions = ['pull_user_unpost_trades', 'autolist_user_items', 'pull_user_items',
               'sync_online_prodnum_to_offline', 'async_pull_lastest_trades']


admin.site.register(User, UserAdmin)


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'nick', 'name', 'buy_times', 'avg_payment', 'last_buy_time',
                    'city', 'state', 'district', 'is_valid')
    list_display_links = ('id', 'nick')

    ordering = ['-last_buy_time']

    list_filter = ('is_valid', 'sex', ('last_buy_time', DateFieldListFilter))
    search_fields = ['nick', 'name']

    def export_distinct_mobile_action(self, request, queryset):
        """ 导出唯一号码 """

        dt = datetime.datetime.now()
        queryset = queryset.filter(is_valid=True)
        mobile_tuple = gen_cvs_tuple(queryset,
                                     fields=['mobile', ],
                                     title=[u'手机'])

        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') > -1
        file_name = u'mobile-%s-%s.csv' % (dt.month, dt.day)

        myfile = StringIO.StringIO()

        writer = CSVUnicodeWriter(myfile, encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(mobile_tuple)

        response = HttpResponse(myfile.getvalue(), content_type='application/octet-stream')
        myfile.close()
        response['Content-Disposition'] = 'attachment; filename=%s' % file_name

        return response

    export_distinct_mobile_action.short_description = u"导出手机号码"

    actions = ['export_distinct_mobile_action']


admin.site.register(Customer, CustomerAdmin)
