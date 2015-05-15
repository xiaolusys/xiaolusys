#-*- coding:utf8 -*-
from django.contrib import admin
from flashsale.xiaolumm.models import UserGroup

from shopback.base.options import DateFieldListFilter
from .models import Clicks,XiaoluMama,AgencyLevel,CashOut,CarryLog

from . import forms 

class XiaoluMamaAdmin(admin.ModelAdmin):
    
    user_groups = []
    
    form = forms.XiaoluMamaForm
    list_display = ('id','mobile','province','get_cash_display','get_pending_display',
                    'weikefu','agencylevel','charge_link','group_select','created','status')
    list_filter = ('agencylevel','manager','status','charge_status',('created',DateFieldListFilter),'user_group')
    search_fields = ['id','mobile','manager','weikefu','openid']
    
    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        default_code = ['BLACK','NORMAL']
        default_code.append(request.user.username)
        
        self.user_groups = UserGroup.objects.filter(code__in=default_code)

        return super(XiaoluMamaAdmin,self).get_changelist(request,**kwargs)
    
    def group_select(self, obj):

        categorys = set(self.user_groups)

        if obj.user_group:
            categorys.add(obj.user_group)

        cat_list = ["<select class='group_select' gid='%s'>"%obj.id]
        cat_list.append("<option value=''>-------------------</option>")
        for cat in categorys:

            if obj and obj.user_group == cat:
                cat_list.append("<option value='%s' selected>%s</option>"%(cat.id,cat))
                continue

            cat_list.append("<option value='%s'>%s</option>"%(cat.id,cat))
        cat_list.append("</select>")

        return "".join(cat_list)
    
    group_select.allow_tags = True
    group_select.short_description = u"所属群组"
    
    def charge_link(self, obj):

        if obj.charge_status == XiaoluMama.CHARGED:
            return u'[ %s ]' % obj.manager_name
        
        if obj.charge_status == XiaoluMama.FROZEN:
            return obj.get_charge_status_display()

        return ('<a href="javascript:void(0);" class="btn btn-primary btn-charge" '
                + 'style="color:white;" sid="{0}">接管</a></p>'.format(obj.id))
        
    charge_link.allow_tags = True
    charge_link.short_description = u"接管信息"
    
    
    class Media:
        css = {"all": ("admin/css/forms.css","css/admin/dialog.css"
                       ,"css/admin/common.css", "jquery/jquery-ui-1.10.1.css")}
        js = ("js/admin/adminpopup.js","js/xlmm_change_list.js")
    
    
admin.site.register(XiaoluMama, XiaoluMamaAdmin) 
    

class AgencyLevelAdmin(admin.ModelAdmin):
    
    list_display = ('category','deposit','cash','get_basic_rate_display','target','get_extra_rate_display','created')
    search_fields = ['category']
    
admin.site.register(AgencyLevel, AgencyLevelAdmin) 


class ClicksAdmin(admin.ModelAdmin):
    list_display = ('linkid','openid','isvalid','created')
    list_filter = ('isvalid',('created',DateFieldListFilter),)
    search_fields = ['openid',]

admin.site.register(Clicks, ClicksAdmin) 


class CashOutAdmin(admin.ModelAdmin):
    
    form = forms.CashOutForm
    list_display = ('xlmm','get_value_display','status','created')
    list_filter  = ('status',)
    search_fields = ['xlmm']
    
admin.site.register(CashOut, CashOutAdmin) 


class CarryLogAdmin(admin.ModelAdmin):
    
    form = forms.CarryLogForm
    list_display = ('xlmm', 'buyer_nick', 'get_value_display', 'log_type', 'carry_type', 'status', 'created')
    list_filter = ('log_type','carry_type','status')
    search_fields = ['xlmm', 'buyer_nick']

admin.site.register(CarryLog, CarryLogAdmin)
