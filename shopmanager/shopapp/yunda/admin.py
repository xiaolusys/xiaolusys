#-*- coding:utf8 -*-
from django.contrib import admin
from shopapp.yunda.models import ClassifyZone,BranchZone,LogisticOrder,LogisticCustomer,\
    TodaySmallPackageWeight,TodayParentPackageWeight
from shopback.base.options import DateFieldListFilter

class ClassifyZoneInline(admin.TabularInline):
    
    model = ClassifyZone
    fields = ('state','city','district')
    


class ClassifyZoneAdmin(admin.ModelAdmin):
    
    list_display = ('state','city','district','branch')
    list_display_links = ('state','city',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    search_fields = ['state','city','district']


admin.site.register(ClassifyZone,ClassifyZoneAdmin)


class BranchZoneAdmin(admin.ModelAdmin):
    
    list_display = ('code','name','barcode')
    list_display_links = ('code','name',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    inlines = [ClassifyZoneInline]
    
    search_fields = ['code','name','barcode']


admin.site.register(BranchZone,BranchZoneAdmin)


class LogisticCustomerAdmin(admin.ModelAdmin):
    
    list_display = ('cus_id','name','code','company_name','qr_id','lanjian_id','ludan_id','sn_code',
                    'device_code','contacter','mobile','status','memo')
    list_display_links = ('name','company_name',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    list_filter = ('status',)
    search_fields = ['cus_id','name','code','sync_addr','company_name','contacter']


admin.site.register(LogisticCustomer,LogisticCustomerAdmin)

class TodaySmallPackageWeightAdmin(admin.ModelAdmin):
    
    list_display = ('package_id','parent_package_id','weight','upload_weight','weighted','is_jzhw')
    list_display_links = ('package_id','parent_package_id',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    list_filter = ('is_jzhw',)
    search_fields = ['package_id','parent_package_id']


admin.site.register(TodaySmallPackageWeight,TodaySmallPackageWeightAdmin)


class TodayParentPackageWeightAdmin(admin.ModelAdmin):
    
    list_display = ('cus_oid','customer','out_sid','weight','receiver_name','receiver_state','receiver_city',
                    'receiver_mobile','weighted','created','is_charged','sync_addr','status')
    list_display_links = ('out_sid','cus_oid',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    list_filter = ('status','is_charged','sync_addr',('weighted',DateFieldListFilter),('created',DateFieldListFilter))
    search_fields = ['cus_oid','out_sid','receiver_name','receiver_mobile','receiver_phone']


admin.site.register(TodayParentPackageWeight,TodayParentPackageWeightAdmin)


class LogisticOrderAdmin(admin.ModelAdmin):
    
    list_display = ('cus_oid','customer','out_sid','weight','receiver_name','receiver_state','receiver_city',
                    'receiver_mobile','weighted','created','is_charged','sync_addr','status')
    list_display_links = ('out_sid','cus_oid',)

    #date_hierarchy = 'created'
    #ordering = ['created_at']
    
    list_filter = ('status','is_charged','sync_addr',('weighted',DateFieldListFilter),('created',DateFieldListFilter))
    search_fields = ['cus_oid','out_sid','receiver_name','receiver_mobile','receiver_phone']


admin.site.register(LogisticOrder,LogisticOrderAdmin)



