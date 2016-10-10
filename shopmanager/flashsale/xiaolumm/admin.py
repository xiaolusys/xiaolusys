# encoding:utf-8
import datetime

from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Sum

from core.admin import ApproxAdmin
from core.filters import DateFieldListFilter
from flashsale.clickcount.models import ClickCount
from flashsale.clickrebeta.models import StatisticsShoppingByDay
from flashsale.xiaolumm.models import (
    XiaoluMama,
    AgencyLevel,
    CashOut,
    CarryLog,
    OrderRedPacket,
    MamaDayStats,
    PotentialMama,
    MamaDailyAppVisit,
    MamaTabVisitStats,
    MamaDeviceStats,
    MamaDailyTabVisit,
    MamaMission,
    MamaMissionRecord,
    RankActivity,
    MamaAdministrator,
    WeixinPushEvent
)
from flashsale.xiaolumm.models.message import XlmmMessage, XlmmMessageRel
from flashsale.xiaolumm.models.models_advertis import MamaVebViewConf
from . import forms
from .filters import UserNameFilter
from .models.models_rebeta import AgencyOrderRebetaScheme
from flashsale.xiaolumm.models.carry_total import MamaCarryTotal, MamaTeamCarryTotal, TeamCarryTotalRecord, \
    CarryTotalRecord
from flashsale.xiaolumm.models.score import XlmmEffectScore, XlmmTeamEffScore

class XiaoluMamaAdmin(ApproxAdmin):
    user_groups = []

    form = forms.XiaoluMamaForm
    list_display = (
        'id', 'customer_id', 'mama_data_display', 'get_cash_display', 'total_inout_item', 'last_renew_type',
        'agencylevel',
        'charge_link', 'group_select', 'click_state', 'exam_pass', 'progress', 'hasale', 'charge_time',
        'status', 'referal_from', 'mama_Verify')
    list_filter = (
        'progress', 'agencylevel', 'last_renew_type', 'manager', 'status', 'charge_status', 'hasale',
        ('charge_time', DateFieldListFilter),)
        #'user_group')
    list_display_links = ('id', 'mama_data_display',)
    search_fields = ['=id', '=mobile', '=manager', 'weikefu', '=openid', '=referal_from']
    list_per_page = 25

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = self.readonly_fields
        if not request.user.is_superuser:
            readonly_fields = readonly_fields + ('mobile', 'openid', 'lowest_uncoushout', 'charge_time',
                                                 'charge_status', 'referal_from')
        return readonly_fields

    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        from shopapp.weixin.models import UserGroup
        default_code = ['BLACK', 'NORMAL']
        default_code.append(request.user.username)

        self.user_groups = UserGroup.objects.filter(code__in=default_code)

        return super(XiaoluMamaAdmin, self).get_changelist(request, **kwargs)

    def group_select(self, obj):

        categorys = set(self.user_groups)

        if obj.user_group:
            categorys.add(obj.user_group)

        cat_list = ["<select class='group_select' gid='%s'>" % obj.id]
        cat_list.append("<option value=''>-------------------</option>")
        for cat in categorys:

            if obj and obj.user_group == cat:
                cat_list.append("<option value='%s' selected>%s</option>" % (cat.id, cat))
                continue

            cat_list.append("<option value='%s'>%s</option>" % (cat.id, cat))
        cat_list.append("</select>")

        return "".join(cat_list)

    group_select.allow_tags = True
    group_select.short_description = u"所属群组"

    def total_inout_item(self, obj):

        mm_clogs = CarryLog.objects.filter(xlmm=obj.id)  # .exclude(log_type=CarryLog.ORDER_RED_PAC)

        income_qs = mm_clogs.filter(carry_type=CarryLog.CARRY_IN, status=CarryLog.CONFIRMED)
        total_income = income_qs.aggregate(total_value=Sum('value')).get('total_value') or 0

        outcome_qs = mm_clogs.filter(carry_type=CarryLog.CARRY_OUT, status=CarryLog.CONFIRMED)
        total_pay = outcome_qs.aggregate(total_value=Sum('value')).get('total_value') or 0

        return (u'<div><p>总收入：%s</p><p>总支出：%s</p></div>' % (total_income / 100.0, total_pay / 100.0))

    total_inout_item.allow_tags = True
    total_inout_item.short_description = u"总收入/支出"

    def charge_link(self, obj):
        if obj.charge_status == XiaoluMama.CHARGED:
            return u'%s' % obj.manager_name

        if obj.charge_status == XiaoluMama.FROZEN:
            return obj.get_charge_status_display()
        return (u'未接管')
        # return ('<a href="javascript:void(0);" class="btn btn-primary btn-charge" '
        # + 'style="color:white;" sid="{0}">接管</a></p>'.format(obj.id))
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
        return (
            u'<div><a style="display:block;" href="/admin/xiaolumm/statisticsshopping/?shoptime__gte=%s&linkid=%s&">今日订单</a>' % (
                dt, obj.id) +
            u'<br><a style="display:block;" href="/admin/xiaolumm/clicks/?click_time__gte=%s&linkid=%s">今日点击</a></div>' % (
                dt, obj.id))

    click_state.allow_tags = True
    click_state.short_description = u"妈妈统计"

    def mama_Verify(self, obj):
        from flashsale.xiaolumm.views.views import get_Deposit_Trade

        trade = get_Deposit_Trade(obj.openid, obj.mobile)
        if obj.manager == 0 and obj.charge_status == XiaoluMama.UNCHARGE and trade is not None:  # 该代理没有管理员 并且没有被接管
            return (
                u'<button type="button" id="daili_{0}" class="btn btn-warning btn-xs" data-toggle="modal" data-target=".bs-example-modal-sm_mama_verify{0}">代理审核</button> '
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
        css = {"all": ("admin/css/forms.css", "css/admin/dialog.css"
                       , "css/admin/common.css", "jquery/jquery-ui-1.10.1.css", "bootstrap/css/bootstrap3.2.0.min.css",
                       "css/mama_profile.css")}
        js = (
            "js/admin/adminpopup.js", "js/xlmm_change_list.js", "bootstrap/js/bootstrap-3.2.0.min.js",
            "js/mama_vrify.js")


admin.site.register(XiaoluMama, XiaoluMamaAdmin)


class AgencyLevelAdmin(admin.ModelAdmin):
    list_display = (
        'category', 'deposit', 'cash', 'get_basic_rate_display', 'target', 'get_extra_rate_display', 'created')
    search_fields = ['category']


admin.site.register(AgencyLevel, AgencyLevelAdmin)


class CashOutAdmin(ApproxAdmin):
    form = forms.CashOutForm
    list_display = ('id', 'xlmm', 'get_cashout_verify', 'get_value_display', 'get_xlmm_history_cashin',
                    'get_xlmm_history_cashout', 'get_xlmm_history_cashout_record', 'fortune_cash_num_display',
                    'get_xlmm_total_click', 'cash_out_type', 'date_field', 'uni_key',
                    'get_xlmm_total_order', 'status', 'approve_time', 'created', 'get_cash_out_xlmm_manager')
    list_filter = ('cash_out_type',
                   'status',
                   ('approve_time', DateFieldListFilter), ('created', DateFieldListFilter), UserNameFilter)
    search_fields = ['=id', '=xlmm']
    list_per_page = 15

    def fortune_cash_num_display(self, obj):
        """妈妈财富表的余额"""
        try:
            fortune = MamaFortune.objects.get(mama_id=obj.xlmm)
        except Exception, exc:
            return '暂无财富记录'
        if obj.status == CashOut.PENDING:  # 如果是待审核状态
            return fortune.cash_num_display() + (obj.value * 0.01)  # 未出账余额 = 财富余额(是扣除待提现金额) + 待提现金额
        else:  # 其他状态
            return fortune.cash_num_display()  # 未出账余额 = 财富余额

    fortune_cash_num_display.allow_tags = True
    fortune_cash_num_display.short_description = u"未出账余额"

    def get_cashout_verify(self, obj):
        # return obj.xlmm  # 返回id号码
        if obj.status == CashOut.PENDING:
            return (u'<a style="display:block;"href="/m/cashoutverify/%d/%d">提现审核</a>' % (obj.xlmm, obj.id))
        elif obj.status == CashOut.APPROVED:
            return (u'<a style="display:block;"href="/admin/xiaolumm/envelop/?receiver=%s">查看红包</a>' % (obj.xlmm))
        return ''

    get_cashout_verify.allow_tags = True
    get_cashout_verify.short_description = u"提现审核"

    # 计算该小鹿妈妈的点击数量并显示
    def get_xlmm_total_click(self, obj):
        clickcounts = ClickCount.objects.filter(linkid=obj.xlmm, date__lt=obj.created)
        sum_click = clickcounts.aggregate(total_click=Sum('valid_num')).get('total_click') or 0
        return sum_click

    get_xlmm_total_click.allow_tags = True
    get_xlmm_total_click.short_description = u"历史有效点击数"

    # 计算该小鹿妈妈的订单数量并显示  tongjidate
    def get_xlmm_total_order(self, obj):
        orders = StatisticsShoppingByDay.objects.filter(linkid=obj.xlmm, tongjidate__lt=obj.created)
        sum_order = orders.aggregate(total_order=Sum('ordernumcount')).get('total_order') or 0
        return sum_order

    get_xlmm_total_order.allow_tags = True
    get_xlmm_total_order.short_description = u"历史订单数"

    # 计算该小鹿妈妈的历史金额  这里修改 属于 提现记录创建的时刻以前的历史总收入  CashOut created   CarryLog created
    def get_xlmm_history_cashin(self, obj):
        # CARRY_TYPE_CHOICES  CARRY_IN
        carrylogs = CarryLog.objects.filter(xlmm=obj.xlmm, carry_type=CarryLog.CARRY_IN, status=CarryLog.CONFIRMED,
                                            created__lt=obj.created)
        sum_carry_in = carrylogs.aggregate(total_carry_in=Sum('value')).get('total_carry_in') or 0
        sum_carry_in = sum_carry_in / 100.0
        return sum_carry_in

    get_xlmm_history_cashin.allow_tags = True
    get_xlmm_history_cashin.short_description = u'历史收入'

    # 计算小鹿妈妈的历史支出（在当次提现记录创建日期之前的总支出）
    def get_xlmm_history_cashout(self, obj):
        # CARRY_TYPE_CHOICES  CARRY_OUT
        carrylogs = CarryLog.objects.filter(xlmm=obj.xlmm, carry_type=CarryLog.CARRY_OUT, status=CarryLog.CONFIRMED,
                                            created__lt=obj.created)
        sum_carry_out = carrylogs.aggregate(total_carry_out=Sum('value')).get('total_carry_out') or 0
        sum_carry_out = sum_carry_out / 100.0
        return sum_carry_out

    get_xlmm_history_cashout.allow_tags = True
    get_xlmm_history_cashout.short_description = u'历史支出'

    # 计算小鹿妈妈的历史审核通过的提现记录（在当次提现记录创建日期之前的总提现金额 求和）
    def get_xlmm_history_cashout_record(self, obj):
        # CARRY_TYPE_CHOICES  CASHOUT
        caskouts = CashOut.objects.filter(xlmm=obj.xlmm, status=CashOut.APPROVED, created__lt=obj.created)
        caskout = caskouts.aggregate(total_carry_out=Sum('value')).get('total_carry_out') or 0
        caskout = caskout / 100.0
        return caskout

    get_xlmm_history_cashout_record.allow_tags = True
    get_xlmm_history_cashout_record.short_description = u'历史提现'

    # 添加妈妈所属管理员字段
    # ----------------------------------------------------------------------
    def get_cash_out_xlmm_manager(self, obj):
        """获取小鹿妈妈的管理员，显示到提现记录列表中"""
        xlmm = XiaoluMama.objects.get(id=obj.xlmm)
        username = User.objects.get(id=xlmm.manager)
        return username

    get_cash_out_xlmm_manager.allow_tags = True
    get_cash_out_xlmm_manager.short_description = u'所属管理员'

    def reject_cashout_bat(self, request, queryset):
        """ 批量处理拒绝提现记录 """
        from core.options import log_action, CHANGE

        pendings = queryset.filter(status=CashOut.PENDING)
        count = 0
        for pending in pendings:
            pending.status = CashOut.REJECTED
            pending.save()
            count += 1
            log_action(request.user, pending, CHANGE, u'批量处理待审核状态到拒绝提现状态')
        return self.message_user(request, '共拒绝%s条记录' % count)

    reject_cashout_bat.short_description = '批量拒绝用户提现'

    actions = ['reject_cashout_bat']


admin.site.register(CashOut, CashOutAdmin)


class CarryLogAdmin(ApproxAdmin):
    form = forms.CarryLogForm
    list_display = ('xlmm', 'buyer_nick', 'get_value_display', 'log_type',
                    'carry_type', 'status', 'carry_date', 'created')
    list_filter = ('log_type', 'carry_type', 'status', ('carry_date', DateFieldListFilter))
    search_fields = ['=xlmm', '=buyer_nick']


admin.site.register(CarryLog, CarryLogAdmin)


class OrderRedPacketAdmin(ApproxAdmin):
    list_display = ('xlmm', 'first_red', 'ten_order_red', 'created', 'modified')
    search_fields = ['=xlmm']


admin.site.register(OrderRedPacket, OrderRedPacketAdmin)

from .forms import MamaDayStatsForm


class MamaDayStatsAdmin(ApproxAdmin):
    list_display = ('xlmm', 'day_date', 'get_base_click_price_display', 'get_lweek_roi_display',
                    'get_tweek_roi_display', 'lweek_clicks', 'lweek_buyers', 'get_lweek_payment_display',
                    'tweek_clicks', 'tweek_buyers', 'get_tweek_payment_display')

    search_fields = ['=xlmm']
    list_filter = (('day_date', DateFieldListFilter),)
    form = MamaDayStatsForm


admin.site.register(MamaDayStats, MamaDayStatsAdmin)

from flashsale.xiaolumm.models.models_advertis import XlmmAdvertis, NinePicAdver


class XlmmAdvertisAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'show_people', 'is_valid', 'start_time', 'end_time', 'created')
    search_fields = ['title', 'id']
    list_filter = ('end_time', 'created', 'is_valid')


admin.site.register(XlmmAdvertis, XlmmAdvertisAdmin)

from django.contrib import messages


class NinePicAdverAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'auther', 'turns_num', 'start_time', 'is_pushed')
    search_fields = ['title', 'id']
    list_filter = ('start_time', 'cate_gory')

    def push_to_mama(self, request, queryset):
        """推送九张图更新消息给代理"""
        from tasks_mama_push import task_push_ninpic_remind

        if queryset.count() == 1:
            ninepic = queryset[0]
            if not ninepic.is_pushed:
                task_push_ninpic_remind.delay(ninepic)
                queryset.update(is_pushed=True)
                return self.message_user(request, u'推送成功')
            else:
                return self.message_user(request, u'已经是推送过了的状态', level=messages.ERROR)
        else:
            return self.message_user(request, u'勾选一个推送项', level=messages.WARNING)

    push_to_mama.short_description = u'推送给代理'
    actions = ['push_to_mama', ]


admin.site.register(NinePicAdver, NinePicAdverAdmin)


class AgencyOrderRebetaSchemeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_default', 'price_active', 'status', 'created', 'modified')
    search_fields = ['name', 'id']
    list_filter = ('is_default', 'price_active', 'status')


admin.site.register(AgencyOrderRebetaScheme, AgencyOrderRebetaSchemeAdmin)

from flashsale.xiaolumm.models.models_fans import FansNumberRecord, XlmmFans


class XlmmFansAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'xlmm', 'xlmm_cusid', 'refreal_cusid', 'fans_cusid', 'thumbnail_display', 'modified', 'created')
    search_fields = ['xlmm', 'xlmm_cusid', 'refreal_cusid', 'fans_cusid']
    list_filter = ['created']

    def thumbnail_display(self, obj):
        html = u'<p>%s</p><img src="%s" style="width:60px; height:60px">' % (obj.fans_nick, obj.fans_thumbnail)
        return html

    thumbnail_display.allow_tags = True
    thumbnail_display.short_description = u"粉丝昵称/头像"


admin.site.register(XlmmFans, XlmmFansAdmin)


class FansNumberRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'xlmm', 'xlmm_cusid', 'fans_num')
    search_fields = ['xlmm', 'xlmm_cusid']


admin.site.register(FansNumberRecord, FansNumberRecordAdmin)

from flashsale.xiaolumm.models.models_fortune import MamaFortune, CarryRecord, OrderCarry, AwardCarry, \
    ClickCarry, ActiveValue, ReferalRelationship, GroupRelationship, ClickPlan, \
    UniqueVisitor, DailyStats
from django.db.models import F
from core.admin import OrderModelAdmin


class MamaFortuneAdmin(OrderModelAdmin):
    list_display = ('mama_id', 'customer_id', 'mama_level', 'mama_agency_level', 'cash_num_display', 'cash_total_display',
                    'carry_pending_display', 'carry_confirmed_display', 'order_num',
                    'fans_num', 'invite_num', 'invite_trial_num', 'invite_all_num', 'active_normal_num',
                    'active_trial_num', 'active_all_num', 'hasale_normal_num', 'hasale_trial_num', 'modified',
                    'created')
    search_fields = ['=mama_id', '=mama_name']
    orderingdict = {'cash_num': (F('carry_confirmed') + F('history_confirmed') - F('carry_cashout'),
                                 F('carry_cashout') - F('carry_confirmed') - F('history_confirmed')),
                    'cash_total': ((F('carry_pending') + F('carry_confirmed') + F('history_pending') + F(
                        'history_confirmed') + F('history_cashout')).desc(),
                                   F('carry_pending') + F('carry_confirmed') + F('history_pending') + F(
                                       'history_confirmed') + F('history_cashout'))
                    }

    def mama_agency_level(self, obj):
        """ show XiaoluMama agencylevel """
        if obj.xlmm:
            return obj.xlmm.get_agencylevel_display()
        return None

    mama_agency_level.short_description = u'Level'
    mama_agency_level.allow_tags = True


admin.site.register(MamaFortune, MamaFortuneAdmin)


class CarryRecordAdmin(admin.ModelAdmin):
    list_display = (
        'mama_id', 'carry_num_display', 'date_field', 'carry_description', 'carry_type', 'status', 'modified',
        'created')
    search_fields = ['=mama_id', '^carry_description']
    list_filter = ('status', 'carry_type', ('created', DateFieldListFilter))


admin.site.register(CarryRecord, CarryRecordAdmin)


class OrderCarryAdmin(admin.ModelAdmin):
    list_display = ('mama_id', 'order_id', 'order_value', 'carry_num', 'carry_type',
                    'carry_plan_name', 'carry_description',
                    'sku_name', 'sku_img', 'contributor_nick',
                    'contributor_id', 'date_field', 'status', 'modified', 'created')
    list_filter = ('status', 'carry_type', ('date_field', DateFieldListFilter), ('created', DateFieldListFilter))
    search_fields = ('=mama_id', '=order_id', '^carry_description', '=contributor_nick',)

    def get_changelist(self, request, **kwargs):
        from .changelist import OrderCarryChangeList

        return OrderCarryChangeList


admin.site.register(OrderCarry, OrderCarryAdmin)


class AwardCarryAdmin(admin.ModelAdmin):
    list_display = ('mama_id', 'carry_num', 'carry_type', 'carry_description', 'contributor_nick',
                    'contributor_img_html', 'contributor_mama_id', 'status', 'date_field', 'is_full_member', 'modified', 'created')
    list_filter = ('status', 'carry_type', ('created', DateFieldListFilter))
    search_fields = ('=mama_id', '=contributor_nick', '^uni_key')

    def contributor_img_html(self, obj):
        return '<img src="%s" style="width:50px;height:50px">' % (obj.contributor_img,)

    contributor_img_html.short_description = u'头像'
    contributor_img_html.allow_tags = True


    def is_full_member(self, obj):
        mama = XiaoluMama.objects.filter(id=obj.mama_id, last_renew_type__gte=XiaoluMama.HALF, charge_status=XiaoluMama.CHARGED).first()
        if not mama:
            return '待续费'
        return ''

    is_full_member.short_description = u'续费状态'
    is_full_member.allow_tags = True
    
        
admin.site.register(AwardCarry, AwardCarryAdmin)


class ClickCarryAdmin(admin.ModelAdmin):
    list_display = ('mama_id', 'click_num', 'init_order_num', 'init_click_price',
                    'init_click_limit', 'confirmed_order_num',
                    'confirmed_click_price', 'confirmed_click_limit', 'total_value',
                    'status', 'date_field', 'modified', 'created')
    search_fields = ('=mama_id',)
    list_filter = ('status', ('created', DateFieldListFilter))


admin.site.register(ClickCarry, ClickCarryAdmin)


class ActiveValueAdmin(admin.ModelAdmin):
    list_display = ('mama_id', 'value_num', 'value_type', 'status', 'date_field', 'modified', 'created')
    search_fields = ('mama_id',)
    list_filter = ('status', 'value_type',)


admin.site.register(ActiveValue, ActiveValueAdmin)


class ReferalRelationshipAdmin(admin.ModelAdmin):
    list_display = (
    'referal_from_mama_id', 'referal_to_mama_id', 'referal_to_mama_nick', 'referal_type', 'status', 'modified',
    'created')
    search_fields = ('referal_from_mama_id', 'referal_to_mama_id',)
    list_filter = ('status', 'referal_type',)


admin.site.register(ReferalRelationship, ReferalRelationshipAdmin)


class GroupRelationshipAdmin(admin.ModelAdmin):
    list_display = (
        'leader_mama_id', 'referal_from_mama_id', 'member_mama_id', 'member_mama_nick', 'referal_type', 'status',
        'modified', 'created')
    search_fields = ('referal_from_mama_id', 'member_mama_id')
    list_filter = ('status', 'referal_type',)


admin.site.register(GroupRelationship, GroupRelationshipAdmin)


class ClickPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'order_rules', 'start_time', 'end_time', 'status', 'default', 'created')
    list_filter = ('default', 'status',)


admin.site.register(ClickPlan, ClickPlanAdmin)


class UniqueVisitorAdmin(admin.ModelAdmin):
    list_display = ('mama_id', 'visitor_nick', 'visitor_img', 'uni_key', 'date_field',
                    'modified', 'created')
    search_fields = ('mama_id', 'visitor_nick')
    list_filter = (('created', DateFieldListFilter),)


admin.site.register(UniqueVisitor, UniqueVisitorAdmin)


class DailyStatsAdmin(admin.ModelAdmin):
    list_display = ('mama_id', 'today_visitor_num', 'today_order_num', 'today_carry_num',
                    'today_active_value', 'date_field', 'modified', 'created')
    search_fields = ('mama_id',)


admin.site.register(DailyStats, DailyStatsAdmin)

from flashsale.xiaolumm.models.models_lesson import LessonTopic, Instructor, Lesson, LessonAttendRecord, \
    TopicAttendRecord


class LessonTopicAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'cover_image', 'description', 'num_attender', 'lesson_type', 'status', 'modified', 'created')
    search_fields = ('title',)
    list_filter = ('lesson_type', 'status', 'is_show')


admin.site.register(LessonTopic, LessonTopicAdmin)


class InstructorAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'introduction', 'num_lesson', 'num_attender', 'status', 'modified', 'created')
    search_fields = ('name', 'introduction',)
    list_filter = ('status',)


admin.site.register(Instructor, InstructorAdmin)


class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor_name', 'num_attender', 'effect_num_attender',
                    'num_score', 'start_time', 'status', 'modified', 'created')
    search_fields = ('title', 'instructor_name',)
    list_filter = ('status',)


admin.site.register(Lesson, LessonAdmin)


class LessonAttendRecordAdmin(admin.ModelAdmin):
    list_display = ('lesson_id', 'title', 'student_nick', 'num_score', 'status', 'modified', 'created')
    search_fields = ('title',)
    list_filter = ('status',)


admin.site.register(LessonAttendRecord, LessonAttendRecordAdmin)


class TopicAttendRecordAdmin(admin.ModelAdmin):
    list_display = ('topic_id', 'title', 'student_nick', 'lesson_attend_record_id', 'status', 'modified', 'created')
    search_fields = ('title',)
    list_filter = ('status',)


admin.site.register(TopicAttendRecord, TopicAttendRecordAdmin)


class PotentialMamaAdmin(admin.ModelAdmin):
    list_display = ("referal_mama",
                    "potential_mama",
                    "thumbnail_display",
                    "uni_key",
                    "is_full_member", "last_renew_type", "modified", "created")

    list_filter = ("is_full_member",
                   'created',
                   'modified')

    search_fields = ("potential_mama",
                     "referal_mama",
                     "nick")

    def thumbnail_display(self, obj):
        return u'<p>%s</p><img src="%s" style="width:50px;height:50px">' % (obj.nick, obj.thumbnail)

    thumbnail_display.short_description = u'昵称/头像'
    thumbnail_display.allow_tags = True


admin.site.register(PotentialMama, PotentialMamaAdmin)


class MamaVebViewConfAdmin(admin.ModelAdmin):
    list_display = ("id", 'version', 'is_valid')

    list_filter = ("is_valid",
                   'created',
                   'modified')
    search_fields = ("version",)


admin.site.register(MamaVebViewConf, MamaVebViewConfAdmin)


class MamaCarryTotalAdmin(admin.ModelAdmin):
    list_display = (
        'stat_time', "mama_id_admin", 'mama_nick_admin', 'thumbnail_pic', 'mobile_admin', 'total_admin',
        'duration_total', 'expect_total', 'history_total', 'history_num', 'duration_num', 'expect_num',
        'total_rank_delay', 'duration_rank_delay', 'de_rank_delay', 'activite_rank_delay'
    )
    list_filter = ()
    search_fields = ("mama",)

    def thumbnail_pic(self, obj):
        return '<img style="width:50px;height:50px;" src="%s"/>' % (obj.thumbnail,)

    thumbnail_pic.short_description = u'头像'
    thumbnail_pic.allow_tags = True

    def mama_nick_admin(self, obj):
        return obj.mama_nick

    mama_nick_admin.short_description = u'昵称'

    def mama_id_admin(self, obj):
        return obj.mama_id

    mama_id_admin.short_description = u'ID'

    def mobile_admin(self, obj):
        return obj.mobile

    mobile_admin.short_description = u'手机'

    def total_admin(self, obj):
        return obj.total

    total_admin.short_description = u'总额'


admin.site.register(MamaCarryTotal, MamaCarryTotalAdmin)


class MamaTeamCarryTotalAdmin(admin.ModelAdmin):
    list_display = ('stat_time', "mama_id", 'mama_nick', 'thumbnail', 'mobile', 'total', 'duration_total',
                    'expect_total', 'num', 'duration_num', 'expect_num', 'last_renew_type',
                    'total_rank_delay', 'duration_rank_delay', 'de_rank_delay', 'activite_rank_delay'
                    )
    list_filter = ()
    search_fields = ("mama",)


admin.site.register(MamaTeamCarryTotal, MamaTeamCarryTotalAdmin)


class CarryTotalRecordAdmin(admin.ModelAdmin):
    list_display = (
        'stat_time', "mama_id", 'duration_total', 'history_total',
        'history_num', 'duration_num', 'carry_records', 'total_rank', 'duration_rank'
    )
    list_filter = ('stat_time',)
    search_fields = ("mama",)


admin.site.register(CarryTotalRecord, CarryTotalRecordAdmin)


class TeamCarryTotalRecordAdmin(admin.ModelAdmin):
    list_display = ('stat_time', "mama_id", 'total', 'duration_total',
                    'num', 'duration_num', 'total_rank', 'duration_rank')
    list_filter = ()
    search_fields = ("mama",)


admin.site.register(TeamCarryTotalRecord, TeamCarryTotalRecordAdmin)


class XlmmMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', "content_link", 'content', 'dest', 'status', 'read_count', 'creator', 'created')
    list_filter = ('status',)
    search_fields = ('id', "title", '=content_link')
    add_form_template = 'admin/xiaolumm/message/add_form.html'
    change_form_template = 'admin/xiaolumm/message/change_form.html'

    def to_mama(self, obj):
        return u'全体小鹿妈妈'

    to_mama.short_description = u'接收人'


admin.site.register(XlmmMessage, XlmmMessageAdmin)


class XlmmMessageRelAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'mama', 'modified', 'created')
    list_filter = ('message',)


admin.site.register(XlmmMessageRel, XlmmMessageRelAdmin)


class MamaDailyAppVisitAdmin(ApproxAdmin):
    list_display = ('id', 'mama_id', 'date_field', 'device_type', 'version', 'user_agent', 'renew_type', 'num_visits', 'modified', 'created')
    list_filter = ('device_type', 'renew_type', ('created', DateFieldListFilter))
    search_fields = ('mama_id', 'version', 'user_agent')


admin.site.register(MamaDailyAppVisit, MamaDailyAppVisitAdmin)


class MamaTabVisitStatsAdmin(ApproxAdmin):
    list_display = ('id', 'stats_tab', 'date_field', 'visit_total', 'modified', 'created')
    list_filter = ('stats_tab', ('created', DateFieldListFilter))
    search_fields = ('stats_tab', 'date_field')


admin.site.register(MamaTabVisitStats, MamaTabVisitStatsAdmin)


class MamaDailyTabVisitAdmin(ApproxAdmin):
    list_display = ('id', 'mama_id', 'stats_tab', 'date_field', 'modified', 'created')
    list_filter = ('stats_tab',('created', DateFieldListFilter))
    search_fields = ('mama_id', 'stats_tab', 'date_field')


admin.site.register(MamaDailyTabVisit, MamaDailyTabVisitAdmin)


class MamaDeviceStatsAdmin(ApproxAdmin):
    list_display = (
        'id', 'device_type', 'date_field', 'num_latest', 'num_outdated', 'outdated_percentage', 'total_visitor',
        'renew_type', 'num_visits', 'total_device_visitor', 'modified', 'created')
    list_filter = ('device_type', 'renew_type', ('created', DateFieldListFilter))
    search_fields = ('device_type', 'date_field')


admin.site.register(MamaDeviceStats, MamaDeviceStatsAdmin)


class MamaMissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'target', 'cat_type', 'kpi_type', 'date_type',
                    'target_value', 'award_amount', 'start_time', 'end_time', 'status')
    list_filter = ('target', 'status', 'cat_type', 'date_type', 'kpi_type')
    search_fields = ('=id', 'name')


admin.site.register(MamaMission, MamaMissionAdmin)


class MamaMissionRecordAdmin(ApproxAdmin):
    list_display = ('id', 'mama_id', 'referal_from_mama_id', 'group_leader_mama_id',
                    'mission', 'year_week', 'target_value', 'finish_value', 'award_amount',
                    'status', 'finish_time', 'created')
    list_filter = ('year_week', 'status', 'mission__cat_type', 'mission__target',
                   'mission__kpi_type', ('finish_time', DateFieldListFilter))
    search_fields = ('=id', '=mama_id', '^mission__name')

admin.site.register(MamaMissionRecord, MamaMissionRecordAdmin)


class RankActivityAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'status', 'note', 'creator', 'created')

admin.site.register(RankActivity, RankActivityAdmin)


class MamaAdministratorAdmin(ApproxAdmin):
    list_display = ( 'mama', 'get_mama_openid', 'get_mama_mobile', 'get_administrator_username', 'get_administrator_nick', 'created') #
    search_fields = ('=mama__id', '=mama__mobile')

    list_per_page = 10

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + ('mama', 'administrator')


    def get_mama_openid(self, obj):
        return obj.mama.openid

    get_mama_openid.short_description = u'妈妈unionid'

    def get_mama_mobile(self, obj):
        return obj.mama.mobile

    get_mama_mobile.short_description = u'妈妈mobile'

    def get_administrator_username(self, obj):
        return obj.administrator.username

    get_administrator_username.short_description = u'管理员账号'

    def get_administrator_nick(self, obj):
        return obj.administrator.nick

    get_administrator_nick.short_description = u'管理员昵称'

admin.site.register(MamaAdministrator, MamaAdministratorAdmin)


class WeixinPushEventAdmin(ApproxAdmin):
    list_display = ('customer_id', 'mama_id', 'uni_key', 'tid', 'event_type', 'date_field', 'params', 'to_url', 'modified', 'created')
    list_filter = ('event_type', 'tid', ('created', DateFieldListFilter))
    search_fields = ('customer_id', )

admin.site.register(WeixinPushEvent, WeixinPushEventAdmin)


class XlmmEffectScoreAdmin(admin.ModelAdmin):
    list_display = ('mama_id', 'score', 'stat_time', 'created', 'modified')
    list_filter = (('created', DateFieldListFilter),)
    search_fields = ('mama_id', )

admin.site.register(XlmmEffectScore, XlmmEffectScoreAdmin)


class XlmmTeamEffScoreAdmin(admin.ModelAdmin):
    list_display = ('mama_id', 'score', 'stat_time', 'created', 'modified', 'member_ids')
    list_filter = (('created', DateFieldListFilter),)
    search_fields = ('mama_id', )

admin.site.register(XlmmTeamEffScore, XlmmTeamEffScoreAdmin)