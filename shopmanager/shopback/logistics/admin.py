from django.contrib import admin
from shopback.logistics.models import Logistics,LogisticsCompany

__author__ = 'meixqhi'



class LogisticsCompanyAdmin(admin.ModelAdmin):
    list_display = ('id','code','name','reg_mail_no','priority')
    list_display_links = ('id',)
    #list_editable = ('update_time','task_type' ,'is_success','status')

    #date_hierarchy = 'created'
    #ordering = ['created_at']

    search_fields = ['code','name']


admin.site.register(LogisticsCompany, LogisticsCompanyAdmin)



class LogisticsAdmin(admin.ModelAdmin):
    list_display = ('tid','out_sid','company_name','seller_id','seller_nick','buyer_nick','delivery_start','delivery_end'
                    ,'receiver_name','created','modified','type','freight_payer','seller_confirm','status')
    list_display_links = ('tid','buyer_nick','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter = ('seller_nick','freight_payer','seller_confirm','type','status',)
    search_fields = ['tid','out_sid','buyer_nick','receiver_name']


admin.site.register(Logistics, LogisticsAdmin)