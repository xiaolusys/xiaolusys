from django.contrib import admin
from shopback.amounts.models import TradeAmount, OrderAmount


class TradeAmountAdmin(admin.ModelAdmin):
    list_display = ('tid', 'user', 'total_fee', 'post_fee', 'cod_fee', 'payment', 'buyer_cod_fee', 'seller_cod_fee'
                    , 'express_agency_fee', 'alipay_no', 'commission_fee', 'buyer_obtain_point_fee', 'created',
                    'pay_time', 'end_time')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('user',)
    date_hierarchy = 'pay_time'
    search_fields = ['tid', 'alipay_no']


admin.site.register(TradeAmount, TradeAmountAdmin)


class OrderAmountAdmin(admin.ModelAdmin):
    list_display = ('oid', 'num_iid', 'title', 'sku_id', 'sku_properties_name', 'num', 'price', 'payment'
                    , 'discount_fee', 'adjust_fee', 'promotion_name')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    # list_filter = ('status','is_parent')
    search_fields = ['oid', 'num_iid', 'title', 'sku_properties_name', '']


admin.site.register(OrderAmount, OrderAmountAdmin)
