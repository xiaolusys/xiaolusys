from django.contrib import admin


from .models import Clicks,XiaoluMama,AgencyLevel,CashOut,CarryLog


class XiaoluMamaAdmin(admin.ModelAdmin):
    list_display = ('id','mobile','province','weikefu','agencylevel','manager','created','status')
    list_filter = ('weikefu','agencylevel','manager','status')
    search_fields = ['id','mobile','manager']
    
admin.site.register(XiaoluMama, XiaoluMamaAdmin) 
    

class AgencyLevelAdmin(admin.ModelAdmin):
    list_display = ('category','deposit','cash','basic_rate','target','extra_rate','created')
    search_fields = ['category']
    
admin.site.register(AgencyLevel, AgencyLevelAdmin) 


class ClicksAdmin(admin.ModelAdmin):
    list_display = ('linkid','openid','created')
    list_filter = ('linkid',)
    search_fields = ['openid',]

admin.site.register(Clicks, ClicksAdmin) 


class CashOutAdmin(admin.ModelAdmin):
    list_display = ('xlmm','value','status','created')
    list_filter  = ('status',)
    search_fields = ['xlmm']
    
admin.site.register(CashOut, CashOutAdmin) 


class CarryLogAdmin(admin.ModelAdmin):
    list_display = ('xlmm', 'buyer_nick', 'value', 'status', 'created')
    list_filter = ('status',)
    search_fields = ['xlmm', 'buyer_nick']

admin.site.register(CarryLog, CarryLogAdmin)
