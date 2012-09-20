from django.contrib import admin
from shopback.suppliers.models import SupplierType,Supplier



class SupplierTypeAdmin(admin.ModelAdmin):
    list_display = ('id','type_name','extra_info')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    search_fields = ['id','type_name']


admin.site.register(SupplierType,SupplierTypeAdmin)


class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id','type','supplier_name','contact','phone','mobile','fax','zip_code','email'
                    ,'address','account_bank','account_no','main_page','extra_info')
    #list_editable = ('update_time','task_type' ,'is_success','status')
    
    list_filter = ('type',)
    search_fields = ['id','supplier_name']


admin.site.register(Supplier,SupplierAdmin)