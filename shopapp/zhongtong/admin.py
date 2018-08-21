# coding: utf-8
__author__ = 'timi06'

from django.contrib import admin
from .models import ZTOOrderList, PrintRecord

from html_to_pdf import zprint, lianda
from views import place_order


# 订单列表
class OrderListAdmin(admin.ModelAdmin):
    search_fields = ['id', 'yid', 'cus_oid', 'out_sid', 'receiver_name', 'receiver_state']

    list_display = ('yid', 'out_sid', 'cus_oid', 'type', 'weight', 'consign_time', 'receiver_name', 'receiver_state')

    # 批量下单
    def place_order_action(self, request, queryset):
        for q in queryset:

            print "type:", q.type, "q.sys_status", q.sys_status

            if q.type != "exchange" and q.sys_status != "INVALID" and q.out_sid == "":

                place_order(request, q.cus_oid)

                self.message_user(request, u"已成功下单!")
            else:
                self.message_user(request, u"该订单为退换货、已作废或已下单！")

    place_order_action.short_description = u"下单（可批量）"

    # 批量打印
    def print_order_action(self, request, queryset):
        result_dict = {}
        for p in queryset:

            if p.out_sid != "":
                shuju = zprint(request, p.out_sid)
                result_dict[p.out_sid] = shuju
                self.message_user(request, u"%s已成功打印!" % p.out_sid)
            else:
                self.message_user(request, u"%s还未下单！" % p.out_sid)
        lianda(request, result_dict)
        # return HttpResponseRedirect(request.get_full_path())

    print_order_action.short_description = u"打印（可批量）"

    actions = ['print_order_action', 'place_order_action']


admin.site.register(ZTOOrderList, OrderListAdmin)


# 打印记录
class PrintRecordAdmin(admin.ModelAdmin):
    search_fields = ['id', 'out_sid', 'record_time', 'receiver_name']

    list_display = ('out_sid', 'record_name', 'record_time', 'weight', 'receiver_name', 'receiver_state',
                    'receiver_city', 'receiver_district', 'receiver_address', 'receiver_zip', 'receiver_mobile',
                    'receiver_phone')


admin.site.register(PrintRecord, PrintRecordAdmin)
