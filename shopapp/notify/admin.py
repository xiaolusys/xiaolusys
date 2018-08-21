# -*- coding:utf8 -*-
from django.contrib import admin
from shopapp.notify.models import ItemNotify, TradeNotify, RefundNotify


class ItemNotifyAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'num_iid', 'title', 'sku_id', 'sku_num', 'increment', 'nick',
                    'num', 'price', 'changed_fields', 'modified_time', 'status', 'is_exec')

    # list_editable = ('update_time','task_type' ,'is_success','status')

    def modified_time(self, obj):
        return obj.modified.strftime('%Y-%m-%d %H:%M:%S')

    modified_time.short_description = '修改时间'.decode('utf8')
    modified_time.admin_order_field = 'modified'

    list_filter = ('nick', 'status', 'is_exec')
    search_fields = ['id', 'num_iid', 'nick', 'title']


admin.site.register(ItemNotify, ItemNotifyAdmin)


class TradeNotifyAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'tid', 'oid', 'nick', 'seller_nick', 'buyer_nick', 'payment',
                    'type', 'trade_mark', 'modified_time', 'status', 'is_exec')

    # list_editable = ('update_time','task_type' ,'is_success','status')

    def modified_time(self, obj):
        return obj.modified.strftime('%Y-%m-%d %H:%M:%S')

    modified_time.short_description = '修改时间'.decode('utf8')
    modified_time.admin_order_field = 'modified'

    list_filter = ('seller_nick', 'status', 'is_exec')
    search_fields = ['id', 'tid', 'oid', 'nick', 'buyer_nick']


admin.site.register(TradeNotify, TradeNotifyAdmin)


class RefundNotifyAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'tid', 'oid', 'rid', 'nick', 'seller_nick', 'buyer_nick',
                    'refund_fee', 'modified_time', 'status', 'is_exec')

    # list_editable = ('update_time','task_type' ,'is_success','status')

    def modified_time(self, obj):
        return obj.modified.strftime('%Y-%m-%d %H:%M:%S')

    modified_time.short_description = '修改时间'.decode('utf8')
    modified_time.admin_order_field = 'modified'

    list_filter = ('nick', 'status', 'is_exec')
    search_fields = ['id', 'tid', 'oid', 'rid', 'nick', 'buyer_nick']


admin.site.register(RefundNotify, RefundNotifyAdmin)
