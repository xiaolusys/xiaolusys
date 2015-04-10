from django.contrib import admin


from .models import Clicks,XiaoluMama,AgencyLevel,CashOut


class XiaoluMamaAdmin(admin.ModelAdmin):
    list_display = ('pk','mobile','province','weikefu','agencylevel','created','status')
    list_filter = ('weikefu','agencylevel','status')

admin.site.register(XiaoluMama, XiaoluMamaAdmin) 
    

class AgencyLevelAdmin(admin.ModelAdmin):
    list_display = ('category','deposit','cash','basic_rate','target','extra_rate','created')

admin.site.register(AgencyLevel, AgencyLevelAdmin) 


class ClicksAdmin(admin.ModelAdmin):
    list_display = ('linkid','openid','created')
    list_filter = ('linkid',)

admin.site.register(Clicks, ClicksAdmin) 


class CashOutAdmin(admin.ModelAdmin):
    list_display = ('mobile','value','status','created')
    
admin.site.register(CashOut, CashOutAdmin) 

