#encoding:utf-8
import re
import datetime
from django.contrib import admin
from django.db.models import Q
from flashsale.xiaolumm.models import UserGroup
from django.contrib.admin.views.main import ChangeList

from core.admin import ApproxAdmin
from shopback.base.options import DateFieldListFilter

from .models import (
    XiaoluMama,
    AgencyLevel,
    CashOut,
    CarryLog,
    OrderRedPacket,
    MamaDayStats,
    AgencyOrderRebetaScheme
)
from . import forms 
from flashsale.mmexam.models import Result
from flashsale.clickcount.models import ClickCount
from flashsale.clickrebeta.models import StatisticsShoppingByDay
from django.db.models import Sum
from django.contrib.auth.models import User
from .filters import UserNameFilter


class XiaoluMamaAdmin(ApproxAdmin):
    
    user_groups = []
    
    form = forms.XiaoluMamaForm
    list_display = ('id','mama_data_display','get_cash_display','total_inout_item','weikefu','agencylevel',
                    'charge_link','group_select','click_state','exam_pass','progress','hasale','charge_time','status','referal_from','mama_Verify')
    list_filter = ('progress','agencylevel','manager','status','charge_status','hasale',('charge_time',DateFieldListFilter),'user_group')
    list_display_links = ('id','mama_data_display', )
    search_fields = ['=id','=mobile','=manager','weikefu','=openid','=referal_from']
    list_per_page = 25
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = self.readonly_fields
        if not request.user.is_superuser:
            readonly_fields = readonly_fields+('mobile','openid','lowest_uncoushout','charge_time',
                                               'charge_status','referal_from')
        return readonly_fields
    
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
        if obj.exam_Passed():
            return u'<img src="/static/admin/img/icon-yes.gif"></img>&nbsp;已通过'
        return u'<img src="/static/admin/img/icon-no.gif"></img>&nbsp;未通过' 
        
    exam_pass.allow_tags = True
    exam_pass.short_description = u"考试状态"
    
    def click_state(self, obj):
        dt = datetime.date.today()
        return (u'<div><a style="display:block;" href="/admin/xiaolumm/statisticsshopping/?shoptime__gte=%s&linkid=%s&">今日订单</a>'%(dt,obj.id)+
        u'<br><a style="display:block;" href="/admin/xiaolumm/clicks/?click_time__gte=%s&linkid=%s">今日点击</a></div>'%(dt,obj.id))
        
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

    def mama_data_display(self, obj):
        html = u'<a href="/m/xlmm_info/?id={1}" target="_blank">{0}</a>'
        return html.format(obj.mobile, obj.id)

    mama_data_display.allow_tags = True
    mama_data_display.short_description = u"妈妈信息"
    
    class Media:
        css = {"all": ("admin/css/forms.css","css/admin/dialog.css"
                       ,"css/admin/common.css", "jquery/jquery-ui-1.10.1.css","bootstrap/css/bootstrap3.2.0.min.css","css/mama_profile.css")}
        js = ("js/admin/adminpopup.js","js/xlmm_change_list.js","bootstrap/js/bootstrap-3.2.0.min.js","js/mama_vrify.js")
    
    
admin.site.register(XiaoluMama, XiaoluMamaAdmin) 
    

class AgencyLevelAdmin(admin.ModelAdmin):
    
    list_display = ('category','deposit','cash','get_basic_rate_display','target','get_extra_rate_display','created')
    search_fields = ['category']
    
admin.site.register(AgencyLevel, AgencyLevelAdmin) 


class CashOutAdmin(ApproxAdmin):
    
    form = forms.CashOutForm
    list_display = ('xlmm','get_cashout_verify','get_value_display','get_xlmm_history_cashin','get_xlmm_history_cashout','get_xlmm_history_cashout_record','get_xlmm_total_click','get_xlmm_total_order','status','approve_time','created','get_cash_out_xlmm_manager')
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


class CarryLogAdmin(ApproxAdmin):
    
    form = forms.CarryLogForm
    list_display = ('xlmm', 'buyer_nick', 'get_value_display', 'log_type',
                    'carry_type', 'status', 'carry_date', 'created')
    list_filter = ('log_type','carry_type','status',('carry_date',DateFieldListFilter))
    search_fields = ['=xlmm', '=buyer_nick']
    date_hierarchy = 'carry_date'

admin.site.register(CarryLog, CarryLogAdmin)


class OrderRedPacketAdmin(ApproxAdmin):

    list_display = ('xlmm', 'first_red', 'ten_order_red', 'created', 'modified')
    search_fields = ['=xlmm']

admin.site.register(OrderRedPacket, OrderRedPacketAdmin)


from .forms import MamaDayStatsForm

class MamaDayStatsAdmin(ApproxAdmin):
    
    list_display = ('xlmm', 'day_date', 'get_base_click_price_display','get_lweek_roi_display',
                    'get_tweek_roi_display','lweek_clicks', 'lweek_buyers', 'get_lweek_payment_display',
                    'tweek_clicks' ,'tweek_buyers' ,'get_tweek_payment_display')

    search_fields = ['=xlmm']
    date_hierarchy = 'day_date'
    form = MamaDayStatsForm
    

admin.site.register(MamaDayStats, MamaDayStatsAdmin)


from models_advertis import XlmmAdvertis, NinePicAdver


class XlmmAdvertisAdmin(admin.ModelAdmin):

    list_display = ('id', 'title', 'show_people','is_valid', 'start_time', 'end_time', 'created')
    search_fields = ['title', 'id']
    list_filter = ('end_time', 'created', 'is_valid')


admin.site.register(XlmmAdvertis, XlmmAdvertisAdmin)


class NinePicAdverAdmin(admin.ModelAdmin):

    list_display = ('id', 'title', 'auther', 'turns_num', 'start_time')
    search_fields = ['title', 'id']
    list_filter = ('start_time', 'cate_gory')


admin.site.register(NinePicAdver, NinePicAdverAdmin)

class AgencyOrderRebetaSchemeAdmin(admin.ModelAdmin):

    list_display = ('id', 'name', 'modified', 'is_default', 'status')
    search_fields = ['name', 'id']
    list_filter = ('is_default', 'status')


admin.site.register(AgencyOrderRebetaScheme, AgencyOrderRebetaSchemeAdmin)


from .models_fans import FansNumberRecord, XlmmFans


class XlmmFansAdmin(admin.ModelAdmin):
    list_display = ('id', 'xlmm', 'xlmm_cusid', 'refreal_cusid', 'fans_cusid')
    search_fields = ['xlmm', 'xlmm_cusid', 'refreal_cusid', 'fans_cusid']


admin.site.register(XlmmFans, XlmmFansAdmin)


class FansNumberRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'xlmm', 'xlmm_cusid', 'fans_num')
    search_fields = ['xlmm', 'xlmm_cusid']

admin.site.register(FansNumberRecord, FansNumberRecordAdmin)



from models_fortune import MamaFortune, CarryRecord, OrderCarry, AwardCarry, \
    ClickCarry, ActiveValue, ReferalRelationship, GroupRelationship, ClickPlan, UniqueVisitor
    


class MamaFortuneAdmin(admin.ModelAdmin):
    list_display = ('mama_id', 'mama_name')
    search_fields = ['mama_id', 'mama_name']

admin.site.register(MamaFortune, MamaFortuneAdmin)

class CarryRecordAdmin(admin.ModelAdmin):
    list_display = ('mama_id', 'carry_num_display', 'carry_type', 'status')
admin.site.register(CarryRecord, CarryRecordAdmin)


class OrderCarryAdmin(admin.ModelAdmin):
    list_display = ('mama_id', 'order_id', 'order_value', 'carry_num', 'carry_type', 
                    'sku_name', 'sku_img', 'contributor_nick', 'contributor_img',
                    'contributor_id', 'status')
admin.site.register(OrderCarry, OrderCarryAdmin)


class AwardCarryAdmin(admin.ModelAdmin):
    list_display = ('mama_id', 'carry_num', 'carry_type', 'contributor_nick', 
                    'contributor_img', 'contributor_mama_id', 'status')
admin.site.register(AwardCarry, AwardCarryAdmin)


class ClickCarryAdmin(admin.ModelAdmin):
    list_display = ('mama_id', 'click_num', 'init_order_num', 'init_click_price',
                    'init_click_limit', 'confirmed_order_num',
                    'confirmed_click_price', 'confirmed_click_limit', 'total_value',
                    'status', 'date_field')
admin.site.register(ClickCarry, ClickCarryAdmin)


class ActiveValueAdmin(admin.ModelAdmin):
    list_display = ('mama_id', 'value_num', 'value_type', 'status')
admin.site.register(ActiveValue, ActiveValueAdmin)


class ReferalRelationshipAdmin(admin.ModelAdmin):
    list_display = ('referal_from_mama_id', 'referal_to_mama_id', 'referal_to_mama_nick')
admin.site.register(ReferalRelationship,ReferalRelationshipAdmin)


class GroupRelationshipAdmin(admin.ModelAdmin):
    list_display = ('leader_mama_id', 'referal_from_mama_id', 'member_mama_id', 'member_mama_nick')
admin.site.register(GroupRelationship,GroupRelationshipAdmin)


class ClickPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'order_rules', 'status')
admin.site.register(ClickPlan,ClickPlanAdmin)

class UniqueVisitorAdmin(admin.ModelAdmin):
    list_display = ('mama_id', 'visitor_nick', 'visitor_img')
admin.site.register(UniqueVisitor,UniqueVisitorAdmin)
    
