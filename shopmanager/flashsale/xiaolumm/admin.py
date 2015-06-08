#-*- coding:utf8 -*-
import re
import datetime
from django.contrib import admin
from django.db.models import Q
from flashsale.xiaolumm.models import UserGroup
from django.contrib.admin.views.main import ChangeList

from shopback.base.options import DateFieldListFilter
from .models import Clicks,XiaoluMama,AgencyLevel,CashOut,CarryLog

from . import forms 
from flashsale.mmexam.models import Result

class XiaoluMamaAdmin(admin.ModelAdmin):
    
    user_groups = []
    
    form = forms.XiaoluMamaForm
    list_display = ('id','mobile','province','get_cash_display','get_pending_display',
                    'weikefu','agencylevel','charge_link','group_select','click_state','exam_pass','created','status')
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
    
    
    def exam_pass(self, obj):

        results = Result.objects.filter(daili_user=obj.openid)
        try:
            if results.count() > 0  and results[0].is_Exam_Funished():
                return u'<img src="/static/admin/img/icon-yes.gif"></img>&nbsp;%s' % results[0].get_exam_state_display()
        except Exception,exc:
            print 'debug exam pass:',exc.message

        return u'<img src="/static/admin/img/icon-no.gif"></img>&nbsp;未通过' 
        
    exam_pass.allow_tags = True
    exam_pass.short_description = u"考试状态"
    
    def click_state(self, obj):
        dt = datetime.date.today()
        return (u'<div><a style="display:block;" href="/admin/xiaolumm/statisticsshopping/?shoptime__gte=%s&linkid=%s&">今日订单</a>'%(dt,obj.id)+
        '<br><a style="display:block;" href="/admin/xiaolumm/clicks/?click_time__gte=%s&linkid=%s">今日点击</a></div>'%(dt,obj.id))
        
    click_state.allow_tags = True
    click_state.short_description = u"妈妈统计"
    
    class Media:
        css = {"all": ("admin/css/forms.css","css/admin/dialog.css"
                       ,"css/admin/common.css", "jquery/jquery-ui-1.10.1.css")}
        js = ("js/admin/adminpopup.js","js/xlmm_change_list.js")
    
    
admin.site.register(XiaoluMama, XiaoluMamaAdmin) 
    

class AgencyLevelAdmin(admin.ModelAdmin):
    
    list_display = ('category','deposit','cash','get_basic_rate_display','target','get_extra_rate_display','created')
    search_fields = ['category']
    
admin.site.register(AgencyLevel, AgencyLevelAdmin) 


from shopapp.weixin.models import WXOrder

class ClicksChangeList(ChangeList):
    
    def get_query_set(self,request):
        
        search_q = request.GET.get('q','').strip()
        if search_q :
            (self.filter_specs, self.has_filters, remaining_lookup_params,
             use_distinct) = self.get_filters(request)
            
            qs = self.root_query_set
            for filter_spec in self.filter_specs:
                new_qs = filter_spec.queryset(request, qs)
                if new_qs is not None:
                    qs = new_qs
            
            if re.compile('[\d]{11}').match(search_q):
                openids = WXOrder.objects.filter(receiver_mobile=search_q).values('buyer_openid').distinct()
                openids = [o['buyer_openid'] for o in openids]
           
                qs = qs.filter(openid__in=openids)
                return qs
    
            qs = qs.filter(openid=search_q)
            return qs
        
        return super(ClicksChangeList,self).get_query_set(request)


class ClicksAdmin(admin.ModelAdmin):
    list_display = ('linkid','openid','isvalid','click_time')
    list_filter = ('isvalid',('click_time',DateFieldListFilter),)
    search_fields = ['openid', 'linkid']
    
    def get_changelist(self, request, **kwargs):

        return ClicksChangeList

admin.site.register(Clicks, ClicksAdmin) 


class CashOutAdmin(admin.ModelAdmin):
    
    form = forms.CashOutForm
    list_display = ('xlmm','get_value_display','status','approve_time','created','get_cashout_verify')
    list_filter  = ('status',('approve_time',DateFieldListFilter),('created',DateFieldListFilter))
    search_fields = ['xlmm']

    def get_cashout_verify(self, obj):
        #return obj.xlmm  # 返回id号码
        if obj.status == CashOut.PENDING:
            return (u'<a style="display:block;"href="/m/cashoutverify/%d/%d">提现审核</a>'%(obj.xlmm,obj.id))
        elif obj.status == CashOut.APPROVED:
            return (u'<a style="display:block;"href="/admin/xiaolumm/envelop/?receiver=%s">查看红包</a>'%(obj.xlmm))
        return ''

    get_cashout_verify.allow_tags = True
    get_cashout_verify.short_description = u"提现审核"
    
admin.site.register(CashOut, CashOutAdmin) 


class CarryLogAdmin(admin.ModelAdmin):
    
    form = forms.CarryLogForm
    list_display = ('xlmm', 'buyer_nick', 'get_value_display', 'log_type', 
                    'carry_type', 'status', 'carry_date', 'created')
    list_filter = ('log_type','carry_type','status',('carry_date',DateFieldListFilter))
    search_fields = ['xlmm', 'buyer_nick']

admin.site.register(CarryLog, CarryLogAdmin)


