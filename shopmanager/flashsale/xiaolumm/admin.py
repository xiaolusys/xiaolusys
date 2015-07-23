#coding=utf-8
import re
import datetime
from django.contrib import admin
from django.db.models import Q
from flashsale.xiaolumm.models import UserGroup
from django.contrib.admin.views.main import ChangeList

from shopback.base.admin import MyAdmin
from shopback.base.options import DateFieldListFilter,SimpleListFilter

from .models import Clicks,XiaoluMama,AgencyLevel,CashOut,CarryLog,OrderRedPacket,MamaDayStats
from . import forms 
from flashsale.mmexam.models import Result
from flashsale.clickcount.models import ClickCount
from flashsale.clickrebeta.models import StatisticsShoppingByDay
from django.db.models import Sum
from django.contrib.auth.models import User
from .filters import UserNameFilter


class XiaoluMamaAdmin(MyAdmin):
    
    user_groups = []
    
    form = forms.XiaoluMamaForm
    list_display = ('id','mobile','get_cash_display','total_inout_item','weikefu','agencylevel',
                    'charge_link','group_select','click_state','exam_pass','progress','hasale','charge_time','status','referal_from','mama_Verify')
    list_filter = ('progress','agencylevel','manager','status','charge_status','hasale',('charge_time',DateFieldListFilter),'user_group')
    search_fields = ['=id','=mobile','=manager','weikefu','=openid','=referal_from']
    list_per_page = 25
    
    
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
    
    def total_inout_item(self, obj):
        
        mm_clogs = CarryLog.objects.filter(xlmm=obj.id)#.exclude(log_type=CarryLog.ORDER_RED_PAC)
        
        income_qs =  mm_clogs.filter(carry_type=CarryLog.CARRY_IN,status=CarryLog.CONFIRMED)
        total_income = income_qs.aggregate(total_value=Sum('value')).get('total_value') or 0
        
        outcome_qs = mm_clogs.filter(carry_type=CarryLog.CARRY_OUT,status=CarryLog.CONFIRMED)
        total_pay    = outcome_qs.aggregate(total_value=Sum('value')).get('total_value') or 0
    
        return (u'<div><p>总收入：%s</p><p>总支出：%s</p></div>'%(total_income / 100.0, total_pay / 100.0))
    
    total_inout_item.allow_tags = True
    total_inout_item.short_description = u"总收入/支出"
    
    def charge_link(self, obj):

        if obj.charge_status == XiaoluMama.CHARGED:
            return u'%s' % obj.manager_name
        
        if obj.charge_status == XiaoluMama.FROZEN:
            return obj.get_charge_status_display()
        return (u'未接管')
        # return ('<a href="javascript:void(0);" class="btn btn-primary btn-charge" '
        #         + 'style="color:white;" sid="{0}">接管</a></p>'.format(obj.id))
        #
    charge_link.allow_tags = True
    charge_link.short_description = u"管理员"
    
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


    def mama_Verify(self, obj):
        from .views import get_Deposit_Trade
        trade = get_Deposit_Trade(obj.openid, obj.mobile)
        if obj.manager == 0 and obj.charge_status == XiaoluMama.UNCHARGE and trade is not None:   # 该代理没有管理员 并且没有被接管
            return (u'<button type="button" id="daili_{0}" class="btn btn-warning btn-xs" data-toggle="modal" data-target=".bs-example-modal-sm_mama_verify{0}">代理审核</button> '
                    u'<div id="mymodal_{0}" class="modal fade bs-example-modal-sm_mama_verify{0}" tabindex="-1" role="dialog" aria-labelledby="motaikuang{0}">'
                    u'<div class="modal-dialog modal-sm">'
                    u'<div class="modal-content" >'

                    u'<div class="input-group">'
                    u'<input type="text" id="weikefu_{0}" class="form-control" placeholder="昵称" aria-describedby="basic-addon3">'
                    u'<input type="text" id="tuijianren_{0}" class="form-control" placeholder="推荐人手机" aria-describedby="basic-addon2">'
                    u'<span class="input-group-addon" id="bt_verify_{0}" onclick="mama_verify({0})">确定审核</span>'
                    u'</div>'

                    u'</div>'
                    u'</div>'
                    u'</div>'.format(obj.id))
        if obj.manager == 0 and obj.charge_status == XiaoluMama.UNCHARGE and trade is None:
            return (u'没有交押金')
        else:
            return (u'已经审核')
    mama_Verify.allow_tags = True
    mama_Verify.short_description = u"妈妈审核"
    
    class Media:
        css = {"all": ("admin/css/forms.css","css/admin/dialog.css"
                       ,"css/admin/common.css", "jquery/jquery-ui-1.10.1.css","bootstrap/css/bootstrap3.2.0.min.css","css/mama_profile.css")}
        js = ("js/admin/adminpopup.js","js/xlmm_change_list.js","bootstrap/js/bootstrap-3.2.0.min.js","js/mama_vrify.js")
    
    
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


class ClicksAdmin(MyAdmin):
    list_display = ('linkid','openid','isvalid','click_time')
    list_filter = ('isvalid',('click_time',DateFieldListFilter),)
    search_fields = ['=openid', '=linkid']
    
    def get_changelist(self, request, **kwargs):

        return ClicksChangeList

admin.site.register(Clicks, ClicksAdmin) 


class CashOutAdmin(admin.ModelAdmin):
    
    form = forms.CashOutForm
    list_display = ('xlmm','get_value_display','get_xlmm_history_cashin','get_xlmm_history_cashout','get_xlmm_history_cashout_record','get_xlmm_total_click','get_xlmm_total_order','status','approve_time','created','get_cashout_verify','get_cash_out_xlmm_manager')
    list_filter  = ('status',('approve_time',DateFieldListFilter),('created',DateFieldListFilter), UserNameFilter)
    search_fields = ['=xlmm']

    def get_cashout_verify(self, obj):
        #return obj.xlmm  # 返回id号码
        if obj.status == CashOut.PENDING:
            return (u'<a style="display:block;"href="/m/cashoutverify/%d/%d">提现审核</a>'%(obj.xlmm,obj.id))
        elif obj.status == CashOut.APPROVED:
            return (u'<a style="display:block;"href="/admin/xiaolumm/envelop/?receiver=%s">查看红包</a>'%(obj.xlmm))
        return ''
    
    get_cashout_verify.allow_tags = True
    get_cashout_verify.short_description = u"提现审核"

    # 计算该小鹿妈妈的点击数量并显示
    def get_xlmm_total_click(self,obj):
        clickcounts = ClickCount.objects.filter(linkid=obj.xlmm, date__lt=obj.created)
        sum_click = clickcounts.aggregate(total_click=Sum('valid_num')).get('total_click') or 0
        return sum_click
    
    get_xlmm_total_click.allow_tags = True
    get_xlmm_total_click.short_description = u"历史有效点击数"

    # 计算该小鹿妈妈的订单数量并显示  tongjidate
    def get_xlmm_total_order(self,obj):
        orders = StatisticsShoppingByDay.objects.filter(linkid=obj.xlmm, tongjidate__lt=obj.created)
        sum_order = orders.aggregate(total_order=Sum('ordernumcount')).get('total_order') or 0
        return sum_order
    
    get_xlmm_total_order.allow_tags = True
    get_xlmm_total_order.short_description = u"历史订单数"

    # 计算该小鹿妈妈的历史金额  这里修改 属于 提现记录创建的时刻以前的历史总收入  CashOut created   CarryLog created
    def get_xlmm_history_cashin(self,obj):
        # CARRY_TYPE_CHOICES  CARRY_IN
        carrylogs = CarryLog.objects.filter(xlmm=obj.xlmm,carry_type=CarryLog.CARRY_IN,status=CarryLog.CONFIRMED, created__lt= obj.created)
        sum_carry_in = carrylogs.aggregate(total_carry_in=Sum('value')).get('total_carry_in') or 0
        sum_carry_in = sum_carry_in/100.0
        return sum_carry_in
    
    get_xlmm_history_cashin.allow_tags = True
    get_xlmm_history_cashin.short_description = u'历史收入'

    # 计算小鹿妈妈的历史支出（在当次提现记录创建日期之前的总支出）
    def get_xlmm_history_cashout(self,obj):
        # CARRY_TYPE_CHOICES  CARRY_OUT
        carrylogs = CarryLog.objects.filter(xlmm=obj.xlmm,carry_type=CarryLog.CARRY_OUT,status=CarryLog.CONFIRMED, created__lt= obj.created)
        sum_carry_out = carrylogs.aggregate(total_carry_out=Sum('value')).get('total_carry_out') or 0
        sum_carry_out = sum_carry_out/100.0
        return sum_carry_out

    get_xlmm_history_cashout.allow_tags = True
    get_xlmm_history_cashout.short_description = u'历史支出'

    # 计算小鹿妈妈的历史审核通过的提现记录（在当次提现记录创建日期之前的总提现金额 求和）
    def get_xlmm_history_cashout_record(self,obj):
        # CARRY_TYPE_CHOICES  CASHOUT
        caskouts = CashOut.objects.filter(xlmm=obj.xlmm, status=CashOut.APPROVED, created__lt=obj.created)
        caskout = caskouts.aggregate(total_carry_out=Sum('value')).get('total_carry_out') or 0
        caskout = caskout/100.0
        return caskout

    get_xlmm_history_cashout_record.allow_tags = True
    get_xlmm_history_cashout_record.short_description = u'历史提现'
    
    # 添加妈妈所属管理员字段
    #----------------------------------------------------------------------
    def  get_cash_out_xlmm_manager(self,obj):
        """获取小鹿妈妈的管理员，显示到提现记录列表中"""
        xlmm = XiaoluMama.objects.get(id=obj.xlmm)
        username = User.objects.get(id=xlmm.manager)
        return username
    
    get_cash_out_xlmm_manager.allow_tags = True
    get_cash_out_xlmm_manager.short_description = u'所属管理员'

    
admin.site.register(CashOut, CashOutAdmin) 


class CarryLogAdmin(MyAdmin):
    
    form = forms.CarryLogForm
    list_display = ('xlmm', 'buyer_nick', 'get_value_display', 'log_type', 
                    'carry_type', 'status', 'carry_date', 'created')
    list_filter = ('log_type','carry_type','status',('carry_date',DateFieldListFilter))
    search_fields = ['=xlmm', '=buyer_nick']
    date_hierarchy = 'carry_date'

admin.site.register(CarryLog, CarryLogAdmin)


class OrderRedPacketAdmin(admin.ModelAdmin):

    list_display = ('xlmm', 'first_red', 'ten_order_red', 'created', 'modified')
    search_fields = ['=xlmm']

admin.site.register(OrderRedPacket, OrderRedPacketAdmin)


from .forms import MamaDayStatsForm

class MamaDayStatsAdmin(admin.ModelAdmin):
    
    list_display = ('xlmm', 'day_date', 'get_base_click_price_display','get_lweek_roi_display',
                    'get_tweek_roi_display','lweek_clicks', 'lweek_buyers', 'get_lweek_payment_display',
                    'tweek_clicks' ,'tweek_buyers' ,'get_tweek_payment_display')

    search_fields = ['=xlmm']
    date_hierarchy = 'day_date'
    form = MamaDayStatsForm
    

admin.site.register(MamaDayStats, MamaDayStatsAdmin)
