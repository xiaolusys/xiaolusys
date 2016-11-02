from django.contrib import admin
from shopback.logistics.models import Logistics, LogisticsCompany, Area, DestCompany

__author__ = 'meixqhi'


class AreaAdmin(admin.ModelAdmin):
    list_display = ('id', 'parent_id', 'type', 'name', 'zip')
    list_display_links = ('id', 'name')

    # date_hierarchy = 'created'
    # ordering = ['created_at']

    search_fields = ['id', 'parent_id', 'name', 'zip']


admin.site.register(Area, AreaAdmin)


class DestCompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'state', 'city', 'district', 'company')
    list_display_links = ('id', 'state')

    list_filter = ('company',)
    search_fields = ['id', 'state', 'city', 'district']


admin.site.register(DestCompany, DestCompanyAdmin)


class LogisticsCompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'reg_mail_no', 'priority', 'district', 'status')
    list_display_links = ('id', 'code')
    list_editable = ('priority',)

    # date_hierarchy = 'created'
    # ordering = ['created_at']

    search_fields = ['code', 'name', 'district']


admin.site.register(LogisticsCompany, LogisticsCompanyAdmin)


class LogisticsAdmin(admin.ModelAdmin):
    list_display = (
    'tid', 'out_sid', 'company_name', 'seller_id', 'seller_nick', 'buyer_nick', 'delivery_start', 'delivery_end'
    , 'receiver_name', 'created', 'modified', 'type', 'freight_payer', 'seller_confirm', 'status')
    list_display_links = ('tid', 'buyer_nick', 'status')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    # ordering = ['created_at']

    list_filter = ('seller_nick', 'freight_payer', 'seller_confirm', 'type', 'status',)
    search_fields = ['tid', 'out_sid', 'buyer_nick', 'receiver_name']


admin.site.register(Logistics, LogisticsAdmin)
