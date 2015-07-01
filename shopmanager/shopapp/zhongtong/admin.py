# coding: utf-8
__author__ = 'timi06'

from django.contrib import admin
from .models import OrderList, PrintRecord

from .html_to_pdf import runprint
import views

#订单列表
class OrderListAdmin(admin.ModelAdmin):


    search_fields = ['id', 'cus_oid', 'out_sid', 'record_time', 'receiver_name']

    list_display = ('yid','out_sid', 'cus_oid', 'weight', 'receiver_name', 'receiver_state')

    # 批量下单
    def place_order_action(self, requset, queryset):
        for q in queryset:
            views.place_order(requset,q.cus_oid)

    place_order_action.short_description = u"下单（批量）"

    # 批量打印
    def print_order_action(self, request, queryset):
        for p in queryset:
            print "status&out_sid:",p.status,p.out_sid
            if p.status == 1 and p.out_sid != "":

                print p.out_sid,p.receiver_state
                runprint(request,p.out_sid)

                self.message_user(request, u"已成功打印!")
            else:
                self.message_user(request, u"还未下单或已打印！")

        # return HttpResponseRedirect(request.get_full_path())
    print_order_action.short_description = u"打印（批量）"

    actions = ['print_order_action','place_order_action']


admin.site.register(OrderList,OrderListAdmin)

#打印记录
class PrintRecordAdmin(admin.ModelAdmin):


    search_fields = ['id', 'out_sid','record_time','receiver_name']

    list_display = ('out_sid', 'record_name','record_time','weight', 'receiver_name','receiver_state',
                    'receiver_city', 'receiver_district','receiver_address','receiver_zip','receiver_mobile', 'receiver_phone')




admin.site.register(PrintRecord,PrintRecordAdmin)
