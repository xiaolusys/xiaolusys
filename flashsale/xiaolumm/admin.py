# encoding:utf-8
from __future__ import absolute_import, unicode_literals
from django.db.models import F, Sum
from django.contrib import admin, messages
from core.admin import OrderModelAdmin, ApproxAdmin, BaseAdmin
from core.filters import DateFieldListFilter
from core.options import log_action, CHANGE
from flashsale.clickcount.models import ClickCount
from flashsale.clickrebeta.models import StatisticsShoppingByDay, StatisticsShopping

from .models.message import XlmmMessage, XlmmMessageRel
from .models.models_advertis import MamaVebViewConf
from .models.score import XlmmEffectScore, XlmmTeamEffScore
from .models.models_fortune import MamaFortune, CarryRecord, OrderCarry, AwardCarry, ClickCarry, ActiveValue, ReferalRelationship, GroupRelationship, ClickPlan, UniqueVisitor, DailyStats
from .models.carry_total import MamaCarryTotal, MamaTeamCarryTotal, TeamCarryTotalRecord, CarryTotalRecord
from .models.models_lesson import LessonTopic, Instructor, Lesson, LessonAttendRecord, TopicAttendRecord
from .models.models_fans import FansNumberRecord, XlmmFans
from .models.models_advertis import XlmmAdvertis, NinePicAdver
from .models import (
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
    MamaSaleGrade,
    MamaMission,
    MamaMissionRecord,
    RankActivity,
    MamaAdministrator,
    WeixinPushEvent,
    MamaReferalTree,
    EliteMamaStatus,
    XiaoluCoin,
    XiaoluCoinLog
)
from .models.models_rebeta import AgencyOrderRebetaScheme
from .filters import UserNameFilter
from . import forms
from .apis.v1.mamafortune import get_mama_fortune_by_mama_id
from .apis.v1.xiaolumama import get_mama_by_id


class XiaoluMamaAdmin(ApproxAdmin):
    user_groups = []

    form = forms.XiaoluMamaForm
    list_display = ('id', 'customer_id', 'links_display', 'last_renew_type', 'renew_time', 'agencylevel',
                    'progress', 'hasale', 'charge_time', 'status', 'refer_to_mama', 'deposit_infos',
                    'weikefu', 'manager_info')
    list_filter = (
        'progress', 'agencylevel', 'last_renew_type', 'referal_from', 'manager', 'status', 'charge_status', 'hasale',
        ('charge_time', DateFieldListFilter),)
    list_display_links = ('id',)
    search_fields = ['=id', '=mobile', '=manager', 'weikefu', '=openid', '=referal_from']
    list_per_page = 15

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = self.readonly_fields
        groups = list(request.user.groups.values_list('name', flat=True))
        if not (request.user.is_superuser or groups.__contains__('小鹿推广管理员')):
            readonly_fields = readonly_fields + ('mobile', 'openid', 'lowest_uncoushout', 'charge_time',
                                                 'charge_status')
        return readonly_fields

    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        from shopapp.weixin.models import UserGroup

        default_code = ['BLACK', 'NORMAL', request.user.username]

        self.user_groups = UserGroup.objects.filter(code__in=default_code)

        return super(XiaoluMamaAdmin, self).get_changelist(request, **kwargs)

    def group_select(self, obj):

        categorys = set(self.user_groups)

        if obj.user_group:
            categorys.add(obj.user_group)

        cat_list = ["<select class='group_select' gid='%s'>" % obj.id, "<option value=''>-------------------</option>"]
        for cat in categorys:

            if obj and obj.user_group == cat:
                cat_list.append("<option value='%s' selected>%s</option>" % (cat.id, cat))
                continue
            cat_list.append("<option value='%s'>%s</option>" % (cat.id, cat))
        cat_list.append("</select>")

        return "".join(cat_list)

    group_select.allow_tags = True
    group_select.short_description = u"所属群组"

    def refer_to_mama(self, obj):
        # type: () -> text_type
        """推荐人
        """
        r = obj.get_refer_to_relationships()
        f_id = r.referal_from_mama_id if r else ''
        return '<a target="_blank"' \
               'href="/admin/xiaolumm/xiaolumama/?id=%s">%s</a>' % (f_id, f_id)
    refer_to_mama.allow_tags = True
    refer_to_mama.short_description = u"推荐人妈妈"

    def links_display(self, obj):
        # type: (XiaoluMama) -> txt_type
        """相关链接集合
        """
        saletrade = '<a target="_blank" href="/admin/pay/saletrade/?buyer_id=%s">订单</a>' % obj.customer_id
        customer = '<a target="_blank" href="/admin/pay/customer/?id=%s">用户</a>' % obj.customer_id
        coupon = '<a target="_blank" href="/admin/coupon/usercoupon/?customer_id=%s">优惠券</a>' % obj.customer_id
        transcoupon = '<a target="_blank" href="/admin/coupon/coupontransferrecord/?coupon_to_mama_id=%s">精品券</a>' % obj.id
        click = '<a target="_blank" href="/admin/clickcount/clicks/?linkid=%s">点击</a>' % obj.id  # 列表
        fans = '<a target="_blank" href="/admin/xiaolumm/xlmmfans/?xlmm=%s">粉丝</a>' % obj.id  # 粉丝列表
        referal = '<a target="_blank" href="/admin/xiaolumm/referalrelationship/?referal_from_mama_id=%s">邀请</a>' % obj.id
        exam = '<a target="_blank" href="/admin/mmexam/result/?customer_id=%s">考试</a>' % obj.customer_id
        l = [
            saletrade,
            customer,
            coupon,
            transcoupon,
            click,
            fans,
            referal,
            exam
        ]
        return ' | '.join(l)
    links_display.allow_tags = True
    links_display.short_description = u"相关链接"

    def deposit_infos(self, obj):
        # type: (XiaoluMama) -> text_type
        """押金支付信息
        """
        orders = obj.get_deposit_orders().values('sale_trade_id', 'payment')
        payments = [str(i['payment']) for i in orders]
        t_ids = [str(i['sale_trade_id']) for i in orders]
        saletrade = '<a target="_blank" ' \
                    'href="/admin/pay/saletrade/?id__in=%s">%s</a>' % (','.join(t_ids), ' | '.join(payments))
        cashs = obj.get_deposit_cashouts().values('id', 'value')
        vs = [str(k['value'] / 100.0) for k in cashs if k]
        c_ids = [str(j['id']) for j in cashs]
        cashouts = '<a target="_blank" ' \
                   'href="/admin/xiaolumm/cashout/?id__in=%s">%s</a>' % (','.join(c_ids), ' | '.join(vs))
        return saletrade + '<br>' + cashouts

    deposit_infos.allow_tags = True
    deposit_infos.short_description = u"押金单"

    def manager_info(self, obj):
        from django.contrib.auth.models import User

        managers = User.objects.filter(is_staff=True, is_active=True, groups=16)  # 推广组成员
        current_manager = managers.filter(id=obj.manager).first()
        ma_name = current_manager.last_name + current_manager.first_name if current_manager else '选择管理员'
        selected = '<option value="" selected="selected">%s</option>' % ma_name
        options = []
        for manager in managers:
            op = '<option value="%s">%s</option>' % (manager.id, manager.last_name + manager.first_name)
            options.append(op)
        selects = '<select id="select-manager-%s" onchange="changeMamaManager(%s)">%s%s</select>' % (obj.id, obj.id,
                                                                                                     selected,
                                                                                                     ''.join(options))
        return selects

    manager_info.allow_tags = True
    manager_info.short_description = u"归属管理员"

    class Media:
        css = {"all": ("admin/css/forms.css", "css/admin/dialog.css"
                       , "css/admin/common.css", "jquery/jquery-ui-1.10.1.css", "bootstrap/css/bootstrap3.2.0.min.css",
                       "css/mama_profile.css")}
        js = ("js/admin/adminpopup.js",
              '/static/xiaolumm/js/mamaChangeList.js',
              '/static/jquery/jquery-2.1.1.min.js',
              "/static/layer-v1.9.2/layer/layer.js",
              "/static/layer-v1.9.2/layer/extend/layer.ext.js",
              )


admin.site.register(XiaoluMama, XiaoluMamaAdmin)


class AgencyLevelAdmin(admin.ModelAdmin):
    list_display = (
        'category', 'deposit', 'cash', 'get_basic_rate_display', 'target', 'get_extra_rate_display', 'created')
    search_fields = ['category']


admin.site.register(AgencyLevel, AgencyLevelAdmin)


class CashOutAdmin(ApproxAdmin):
    form = forms.CashOutForm
    list_display = ('id', 'xlmm', 'cash_out_type', 'get_value_display', 'fortune_cash',
                    'fortune_carry', 'cash_out_verify', 'total_click', 'total_order', 'date_field',   'status',
                    'approve_time', 'created', 'uni_key')
    list_filter = ('cash_out_type', 'status', ('approve_time', DateFieldListFilter),
                   ('created', DateFieldListFilter), UserNameFilter)
    search_fields = ['=id', '=xlmm']
    list_per_page = 10

    def fortune_cash(self, obj):
        # type: (CashOut)-> float
        """妈妈财富表的余额
        """
        try:
            fortune = get_mama_fortune_by_mama_id(obj.xlmm)
        except MamaFortune.DoesNotExist:
            return u'暂无财富记录'
        if obj.status == CashOut.PENDING:  # 如果是待审核状态
            return fortune.cash_num_display() + (obj.value * 0.01)  # 未出账余额 = 财富余额(是扣除待提现金额) + 待提现金额
        else:  # 其他状态
            return fortune.cash_num_display()  # 未出账余额 = 财富余额

    fortune_cash.allow_tags = True
    fortune_cash.short_description = u"未出账余额"

    def cash_out_verify(self, obj):
        # type: (CashOut) -> text_type
        """进入提现审核页面
        """
        if obj.status == CashOut.PENDING:
            try:
                fortune = get_mama_fortune_by_mama_id(obj.xlmm)
            except MamaFortune.DoesNotExist:
                return u'暂无财富记录'
            pre_cash = fortune.cash_num_display() + (obj.value * 0.01)
            mama = get_mama_by_id(obj.xlmm)
            r = '<input class="cashOut%s"style="padding: 0px 6px" type="button" onclick="rejectCashOut(%s)" value="拒绝"/>' % (obj.id, obj.id)
            if mama.is_cashoutable() and pre_cash * 100 >= obj.value:
                a = '<input class="cashOut%s"style="padding: 0px 6px" type="button" onclick="approveCashOut(%s)" value="通过"/>' % (obj.id, obj.id)
                return '可提%.1f' % pre_cash + a + r
            return '可提%.1f' % pre_cash + r
        elif obj.status == CashOut.APPROVED:
            a = u'<a target="_blank" href="/admin/xiaolumm/envelop/?receiver=%s">总</a>' % obj.xlmm
            s = u'<a target="_blank" href="/admin/xiaolumm/envelop/?referal_id=%s&subject=cashout">单</a>' % obj.id
            return u'红包:' + ' | '.join([a, s])
        return ''

    cash_out_verify.allow_tags = True
    cash_out_verify.short_description = u"审核/查看红包"

    def fortune_carry(self, obj):
        # type: (CashOut) -> float
        """计算小鹿妈妈的历史审核通过的提现记录（在当次提现记录创建日期之前的总提现金额 求和）
        """
        try:
            fortune = get_mama_fortune_by_mama_id(obj.xlmm)
        except MamaFortune.DoesNotExist:
            return u'暂无财富记录'
        carry_in = float(fortune.carry_confirmed + fortune.history_confirmed) / 100.0
        carry_out = float(fortune.carry_cashout) / 100.0
        cash = carry_in - carry_out
        return '%.1f-%.1f=%.1f' % (carry_in, carry_out, cash)

    fortune_carry.allow_tags = True
    fortune_carry.short_description = u'财富收支'

    def total_click(self, obj):
        # type: (CashOut) -> int
        """点击数
        """
        clicks = ClickCount.objects.filter(linkid=obj.xlmm, date__lt=obj.created)
        sum_click = clicks.aggregate(total_click=Sum('valid_num')).get('total_click') or 0
        return sum_click

    total_click.allow_tags = True
    total_click.short_description = u"点击数"

    def total_order(self, obj):
        # type: (CashOut) -> text_type
        """订单数量: 截止提现前订单件数/截止提现前订单笔数/总订单笔数
        """
        orders = StatisticsShoppingByDay.objects.filter(linkid=obj.xlmm, tongjidate__lt=obj.created)
        l_num = orders.aggregate(total_order=Sum('ordernumcount')).get('total_order') or 0
        t_count = StatisticsShopping.objects.filter(linkid=obj.xlmm).count()
        return '/'.join([str(l_num), str(orders.count()), str(t_count)])

    total_order.allow_tags = True
    total_order.short_description = u"订单tN,tC,T"

    def reject_cash_out(self, request, queryset):
        # type: (HttpRequest, List[CashOut])
        """批量处理拒绝提现记录
        """
        count = 0
        for cashout in queryset.filter(status=CashOut.PENDING):
            cashout.reject_cashout()
            count += 1
            log_action(request.user, cashout, CHANGE, u'批量处理待审核状态到拒绝提现状态')
        return self.message_user(request, '共拒绝%s条记录' % count)

    reject_cash_out.short_description = '批量拒绝用户提现'
    actions = ['reject_cash_out']

    class Media:
        css = {"all": ()}
        js = ("/static/js/cashOutVerify.js",
              '/static/jquery/jquery-2.1.1.min.js',
              "/static/layer-v1.9.2/layer/layer.js",
              "/static/layer-v1.9.2/layer/extend/layer.ext.js",)

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


class MamaDayStatsAdmin(ApproxAdmin):
    list_display = ('xlmm', 'day_date', 'get_base_click_price_display', 'get_lweek_roi_display',
                    'get_tweek_roi_display', 'lweek_clicks', 'lweek_buyers', 'get_lweek_payment_display',
                    'tweek_clicks', 'tweek_buyers', 'get_tweek_payment_display')

    search_fields = ['=xlmm']
    list_filter = (('day_date', DateFieldListFilter),)
    form = forms.MamaDayStatsForm


admin.site.register(MamaDayStats, MamaDayStatsAdmin)


class XlmmAdvertisAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'show_people', 'is_valid', 'start_time', 'end_time', 'created')
    search_fields = ['title', 'id']
    list_filter = ('end_time', 'created', 'is_valid')


admin.site.register(XlmmAdvertis, XlmmAdvertisAdmin)


class NinePicAdverAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'auther', 'turns_num', 'start_time', 'is_pushed', 'save_times', 'share_times')
    search_fields = ['title', 'id']
    list_filter = ('start_time', 'cate_gory')

    def push_to_mama(self, request, queryset):
        """推送九张图更新消息给代理"""
        from flashsale.xiaolumm.tasks import task_push_ninpic_remind

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
    search_fields = ['=lmm', '=xlmm_cusid']


admin.site.register(FansNumberRecord, FansNumberRecordAdmin)


class MamaFortuneAdmin(OrderModelAdmin):
    list_display = ('mama_id', 'customer_id', 'mama_level', 'mama_agency_level', 'mama_mobile', 'cash_num_display',
                    'cash_total_display', 'carry_pending_display', 'carry_confirmed_display', 'order_num',
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

    list_filter = ('mama_level', ('created', DateFieldListFilter))

    def mama_agency_level(self, obj):
        """ show XiaoluMama agencylevel """
        if obj.xlmm:
            return obj.xlmm.get_agencylevel_display()
        return None

    mama_agency_level.short_description = u'Level'
    mama_agency_level.allow_tags = True

    def mama_mobile(self, obj):
        from flashsale.pay.models.user import Customer

        if obj.xlmm.customer_id:
            return Customer.objects.filter(id=obj.xlmm.customer_id).first().mobile


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
        'referal_from_mama_id', 'referal_to_mama_id', 'referal_to_mama_nick', 'to_mama_mobile',
        'referal_type', 'status', 'modified', 'created')
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


class MamaSaleGradeAdmin(BaseAdmin):
    list_display = ('mama', 'grade', 'combo_count', 'last_record_time', 'total_finish_count', 'first_finish_time',
                    'created', 'modified')
    list_filter = ('grade',  ('first_finish_time', DateFieldListFilter),  ('created', DateFieldListFilter))
    search_fields = ('=mama',)

admin.site.register(MamaSaleGrade, MamaSaleGradeAdmin)


class MamaMissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'target', 'cat_type', 'kpi_type', 'date_type', 'target_value',
                     'award_amount', 'start_time', 'end_time', 'is_push_msg', 'status')
    list_filter = ('target', 'status', 'cat_type', 'date_type', 'kpi_type', 'is_push_msg')
    search_fields = ('=id', 'name')


admin.site.register(MamaMission, MamaMissionAdmin)


class MamaMissionRecordAdmin(ApproxAdmin):
    list_display = ('id', 'mama_id', 'referal_from_mama_id', 'group_leader_mama_id',
                    'mission', 'year_week', 'target_value', 'finish_value', 'award_amount',
                    'status', 'finish_time', 'created')
    list_filter = ('year_week', 'status', 'mission__cat_type', 'mission__target',
                   'mission__kpi_type', ('finish_time', DateFieldListFilter),('created', DateFieldListFilter))
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


class EliteMamaStatusAdmin(admin.ModelAdmin):
    list_display = ('mama_id', 'sub_mamacount', 'last_active_time', 'status',
                    'saleout_rate', 'transfer_rate', 'refund_rate', 'memo', 'joined_date',
                    'purchase_amount_out', 'purchase_amount_in',
                    'transfer_amount_out', 'transfer_amount_in',
                    'sale_amount_out', 'sale_amount_in',
                    'refund_amount_out', 'refund_amount_in',
                    'return_amount_out', 'return_amount_in',
                    'refund_coupon_out', 'refund_coupon_in',
                    'exchg_amount_out', 'exchg_amount_in',
                    'gift_amount_out', 'gift_amount_in',
                    )
    list_filter = ('status', ('joined_date', DateFieldListFilter), ('last_active_time', DateFieldListFilter),)
    search_fields = ('=mama_id', )

admin.site.register(EliteMamaStatus, EliteMamaStatusAdmin)


class MamaReferalTreeAdmin(admin.ModelAdmin):
    list_display = ('id','referal_to_mama_id_link', 'referal_from_mama_id_link', 'direct_invite_num', 'indirect_invite_num', 'gradient',
                    'direct_fans_num', 'indirect_fans_num', 'fans_gradient', 'is_elite', 'is_vip', 'last_active_time', 'mama_info_link')
    list_filter = ('is_elite', 'is_vip', ('created', DateFieldListFilter), ('last_active_time', DateFieldListFilter), 'gradient')
    search_fields = ('=referal_to_mama_id', '=referal_from_mama_id')

    def referal_to_mama_id_link(self, obj):
        return '<a href="./?q=%s">%s&nbsp;&gt;&gt;</a>'%(obj.referal_to_mama_id, obj.referal_to_mama_id)

    referal_to_mama_id_link.allow_tags = True
    referal_to_mama_id_link.short_description = u'被邀请妈妈ID'

    def referal_from_mama_id_link(self, obj):
        return '<a href="./?q=%s">%s&nbsp;&gt;&gt;</a>' % (obj.referal_from_mama_id, obj.referal_from_mama_id)

    referal_from_mama_id_link.allow_tags = True
    referal_from_mama_id_link.short_description = u'邀请妈妈ID'

    def mama_info_link(self, obj):
        return '<a target="_blank" href="/sale/daystats/yunying/mama/show?mama_id=%s">查看明细</a>' % (obj.referal_from_mama_id,)

    mama_info_link.allow_tags = True
    mama_info_link.short_description = u'妈妈信息'


admin.site.register(MamaReferalTree, MamaReferalTreeAdmin)


class XiaoluCoinAdmin(admin.ModelAdmin):
    list_display = ('id', 'mama_id', 'amount')
    list_filter = ('created',)
    search_fields = ('=mama_id',)

admin.site.register(XiaoluCoin, XiaoluCoinAdmin)


class XiaoluCoinLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'mama_id', 'iro_type', 'subject', 'amount', 'date_field', 'referal_id', 'uni_key')
    list_filter = ('created', 'subject')
    search_fields = ('=mama_id', '=referal_id')

admin.site.register(XiaoluCoinLog, XiaoluCoinLogAdmin)




