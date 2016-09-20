# -*- coding:utf-8 -*-
import re
import urllib
import time
from django.contrib import admin
import cStringIO as StringIO
from django.db import models
from django.http import HttpResponse
from django.conf import settings
from django.contrib.admin.views.main import ChangeList
from django.forms import TextInput, Textarea

from core.admin import ApproxAdmin
from core.filters import DateFieldListFilter
from shopback.items.models import Product
from common.utils import gen_cvs_tuple, CSVUnicodeWriter
from .models_base import (
    WeixinUserInfo,
    WeixinTplMsg,
    WeixinFans,
    WeixinQRcodeTemplate,
)
from shopapp.weixin.models import (WeiXinAccount,
                                   WeixinUnionID,
                                   UserGroup,
                                   WeiXinUser,
                                   WXUserCharge,
                                   WeiXinAutoResponse,
                                   WXProduct,
                                   WXProductSku,
                                   WXOrder,
                                   WXLogistic,
    # ReferalRelationship,
    # ReferalSummary,
                                   ReferalBonusRecord,
                                   Refund,
                                   FreeSample,
                                   SampleOrder,
                                   VipCode,
                                   SampleSku,
                                   Coupon,
                                   CouponClick,
                                   Survey,
                                   SampleChoose,
                                   WeixinUserScore,
                                   WeixinScoreItem,
                                   WeixinClickScore,
                                   WeixinScoreBuy,
                                   WeixinClickScoreRecord)
import logging

logger = logging.getLogger("django.request")


class WeixinUnionIDAdmin(ApproxAdmin):
    list_display = ('openid', 'app_key', 'unionid', 'created')

    list_display_links = ('openid',)

    list_filter = (('created', DateFieldListFilter),)
    search_fields = ['=openid', '=unionid']


admin.site.register(WeixinUnionID, WeixinUnionIDAdmin)


class WeixinUserInfoAdmin(admin.ModelAdmin):
    list_display = ('unionid', 'nick', 'thumbnail', 'modified', 'created')
    search_fields = ('unionid', 'nick')

admin.site.register(WeixinUserInfo, WeixinUserInfoAdmin)


class WeixinTemplateMsg(admin.ModelAdmin):
    list_display = ('wx_template_id', 'header', 'footer', 'content', 'status')

admin.site.register(WeixinTplMsg, WeixinTemplateMsg)


class UserChangeList(ChangeList):
    def get_queryset(self, request):

        # 如果查询条件中含有邀请码
        search_q = request.GET.get('q', '').strip()
        if search_q.isdigit() and len(search_q) in (6, 7, 8):
            vipcodes = VipCode.objects.filter(code=search_q)
            wxuser_ids = [v.owner_openid.id for v in vipcodes]

            return WeiXinUser.objects.filter(id__in=wxuser_ids)

        if re.compile('^[\w]{11}$').match(search_q):
            return WeiXinUser.objects.filter(models.Q(mobile=search_q) | models.Q(vmobile=search_q))

        if re.compile('^[\w-]{24,64}$').match(search_q):
            return WeiXinUser.objects.filter(openid=search_q)

        if search_q:
            return WeiXinUser.objects.none()

        return super(UserChangeList, self).get_queryset(request)


class WeiXinAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'account_id', 'token', 'app_id', 'expires_in',
                    'expired', 'in_voice', 'is_active')

    list_display_links = ('id', 'account_id')

    list_filter = ('is_active', 'in_voice')
    search_fields = ['app_id', 'token', 'partner_id']

    def urlencode(self, value):
        ds = {'s': value}
        return urllib.urlencode(ds)[len('s='):]

    def unicode2Utf8(self, menu):

        if type(menu) == list:
            for m in menu:
                self.unicode2Utf8(m)

        if type(menu) == dict:
            for k, v in menu.iteritems():
                if type(v) == list:
                    self.unicode2Utf8(v)

                if type(v) == unicode:
                    menu[k] = v.encode('utf8')

    def response_change(self, request, obj, *args, **kwargs):
        # 订单处理页面
        opts = obj._meta
        # Handle proxy models automatically created by .only() or .defer()
        verbose_name = opts.verbose_name
        if obj._deferred:
            opts_ = opts.proxy_for_model._meta
            verbose_name = opts_.verbose_name
        pk_value = obj._get_pk_val()
        if obj.jmenu:
            try:
                jmenu = obj.jmenu.copy()
                # self.unicode2Utf8(jmenu)
                from .weixin_apis import WeiXinAPI
                wx_api = WeiXinAPI()
                wx_api.setAccountId(wxpubId=obj.account_id)
                wx_api.createMenu(jmenu)
            except Exception, exc:
                self.message_user(request, u"微信菜单创建失败：%s" % (exc.message or u'请求错误'))
                logger.error(u"微信菜单创建失败：%s" % (exc.message or u'请求错误'), exc_info=True)

        return super(WeiXinAccountAdmin, self).response_change(request, obj, *args, **kwargs)


admin.site.register(WeiXinAccount, WeiXinAccountAdmin)


class UserGroupAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

    search_fields = ['code', 'name']


admin.site.register(UserGroup, UserGroupAdmin)


class WeiXinUserAdmin(ApproxAdmin):
    user_groups = []
    list_per_page = 25
    list_display = ('openid', 'nickname', 'sex', 'province', 'city', 'mobile', 'subscribe'  # ,'referal_count'
                    , 'subscribe_time', 'vipcode_link', 'charge_link', 'group_select', 'isvalid')
    list_display_links = ('openid',)
    list_filter = ('charge_status', 'subscribe', 'isvalid', 'sex', 'user_group',)
    search_fields = ['=openid', '=mobile']

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = self.readonly_fields
        if not request.user.is_superuser:
            readonly_fields = readonly_fields + ('openid', 'unionid', 'charge_status', 'subscribe', 'subscribe_time',
                                                 'validcode', 'vmobile', 'mobile', 'referal_from_openid')
        return readonly_fields

    def charge_link(self, obj):

        if obj.charge_status == WeiXinUser.CHARGED:
            scharge = WXUserCharge.objects.get(wxuser_id=obj.id,
                                               status=WXUserCharge.EFFECT)
            return u'[ %s ]' % scharge.employee.username

        if obj.charge_status == WeiXinUser.FROZEN:
            return obj.get_charge_status_display()

        return ('<a href="javascript:void(0);" class="btn btn-primary btn-charge" '
                + 'style="color:white;" sid="{0}">接管</a></p>'.format(obj.id))

    charge_link.allow_tags = True
    charge_link.short_description = u"接管信息"

    def vipcode_link(self, obj):

        vipcodes = VipCode.objects.filter(owner_openid=obj)
        if vipcodes.count() > 0:
            return vipcodes[0].code
        return '-'

    vipcode_link.allow_tags = True
    vipcode_link.short_description = u"F码"

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

    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        default_code = ['BLACK', 'NORMAL']
        default_code.append(request.user.username)

        self.user_groups = UserGroup.objects.filter(code__in=default_code)

        return UserChangeList

    class Media:
        css = {"all": ("admin/css/forms.css", "css/admin/dialog.css"
                       , "css/admin/common.css", "jquery/jquery-ui-1.10.1.css")}
        js = ("js/admin/adminpopup.js", "js/wxuser_change_list.js")


admin.site.register(WeiXinUser, WeiXinUserAdmin)


class WeiXinAutoResponseAdmin(admin.ModelAdmin):
    list_display = ('message', 'rtype', 'title', 'content', 'fuzzy_match')

    list_filter = ('rtype', 'fuzzy_match')
    search_fields = ['message', 'title', 'content']

    ordering = ('message',)

    formfield_overrides = {
        models.CharField: {'widget': Textarea(attrs={'rows': 5, 'cols': 40})},
        models.FloatField: {'widget': TextInput(attrs={'size': '16'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }


admin.site.register(WeiXinAutoResponse, WeiXinAutoResponseAdmin)


class WXProductAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'product_name', 'sync_stock', 'modified', 'status')

    # --------设置页面布局----------------
    fieldsets = ((u'商品信息:', {
        'classes': ('expand',),
        'fields': (('product_id', 'product_name', 'product_img')
                   , ('product_base',)
                   , ('sku_list',)
                   , ('attrext',)
                   , ('delivery_info',)
                   , ('sync_stock', 'status',)
                   )
    }),
                 )

    list_filter = ('status', ('modified', DateFieldListFilter))
    search_fields = ['product_id', 'product_name']


admin.site.register(WXProduct, WXProductAdmin)


class WXProductSkuAdmin(admin.ModelAdmin):
    list_display = ('sku_id', 'product', 'outer_id', 'outer_sku_id',
                    'sku_name', 'pic_link', 'sku_price', 'ori_price', 'modified', 'status')

    list_filter = ('status', ('modified', DateFieldListFilter))
    search_fields = ['sku_id', 'product__product_id', 'outer_id', 'outer_sku_id']

    def pic_link(self, obj):
        abs_pic_url = obj.sku_img or Product.NO_PIC_PATH
        return (u'<img src="%s" width="100px" height="80px" title="%s"/></a>') % (abs_pic_url,
                                                                                  obj.product.product_name)

    pic_link.allow_tags = True
    pic_link.short_description = "商品图片"


admin.site.register(WXProductSku, WXProductSkuAdmin)


class WXOrderAdmin(ApproxAdmin):
    list_display = ('order_id', 'buyer_nick', 'order_total_price', 'order_create_time',
                    'delivery_id', 'delivery_company', 'order_status')

    list_filter = ('order_status',)
    search_fields = ['=order_id', '=trans_id', '=buyer_nick', '=buyer_openid']

    # --------设置页面布局----------------
    fieldsets = ((u'订单信息:', {
        'classes': ('expand',),
        'fields': (('order_id', 'seller_id', 'trans_id')
                   , ('order_total_price', 'order_express_price', 'order_create_time')
                   , ('buyer_openid', 'buyer_nick', 'order_status')
                   )
    }),
                 (u'商品信息:', {
                     'classes': ('collapse',),
                     'fields': (('product_id', 'product_name', 'product_price')
                                , ('product_sku', 'product_count', 'product_img')
                                )
                 }),
                 (u'收货信息:', {
                     'classes': ('expand',),
                     'fields': (('receiver_name', 'receiver_province', 'receiver_city', 'receiver_zone')
                                , ('receiver_address', 'receiver_mobile', 'receiver_phone')
                                , ('delivery_id', 'delivery_company')
                                )
                 }),
                 )


admin.site.register(WXOrder, WXOrderAdmin)


class WXLogisticAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'origin_code', 'company_code')

    search_fields = ['company_name', 'origin_code', 'company_code']


admin.site.register(WXLogistic, WXLogisticAdmin)


class ReferalRelationshipAdmin(admin.ModelAdmin):
    list_display = ('referal_from_openid', 'referal_to_mobile', 'time_created')

    search_fields = ['referal_from_openid', 'referal_to_mobile']


# admin.site.register(ReferalRelationship, ReferalRelationshipAdmin)


class ReferalSummaryAdmin(admin.ModelAdmin):
    list_display = ('user_openid', 'direct_referal_count', 'indirect_referal_count')

    search_fields = ['user_openid']


# admin.site.register(ReferalSummary, ReferalSummaryAdmin)


class ReferalBonusRecordAdmin(admin.ModelAdmin):
    list_display = ('user_openid', 'referal_user_openid', 'trade_id', 'bonus_value', 'confirmed_status', 'created')

    search_fields = ['user_openid', 'referal_user_openid', 'trade_id']


admin.site.register(ReferalBonusRecord, ReferalBonusRecordAdmin)


class RefundAdmin(admin.ModelAdmin):
    list_display = ('trade_id', 'user_openid', 'refund_type', 'pay_amount', 'vip_code',
                    'review_note', 'pay_note', 'created', 'pay_time', 'refund_status')

    list_filter = ('refund_type', 'refund_status', 'pay_type',
                   ('created', DateFieldListFilter), ('pay_time', DateFieldListFilter))
    search_fields = ['trade_id', 'vip_code', 'user_openid', 'mobile', 'review_note', 'pay_note']

    # 导出商品规格信息
    def export_refund_action(self, request, queryset):
        """ 导出商品及规格信息 """

        from django.core import exceptions
        if not request.user.is_superuser:
            raise exceptions.PermissionDenied

        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') > -1

        csv_fields = ['trade_id', 'user_openid', 'vip_code', 'pay_amount', 'refund_status',
                      'created', 'pay_time', 'refund_type', 'pay_type', 'pay_note']

        csv_title = (u'订单编号', u'用户OPENID', u'邀请码', u'退款金额', u'退款状态'
                     , u'创建日期', u'付款日期', u'返利类型', u'支付方式', u'备注'
                     , u'退款状态(0等待审核,1审核通过,2审核不通过,3完成)'
                     , u'返利类型(1VIP邀请,210积分换购,3满100元返10元,4100元免单,510积分返邮费)')

        pcsv = gen_cvs_tuple(queryset, fields=csv_fields, title=csv_title)

        tmpfile = StringIO.StringIO()
        writer = CSVUnicodeWriter(tmpfile, encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)

        response = HttpResponse(tmpfile.getvalue(), content_type='application/octet-stream')
        tmpfile.close()
        response['Content-Disposition'] = 'attachment; filename=weixin-refund-%s.csv' % str(int(time.time()))

        return response

    export_refund_action.short_description = u"导出退款订单信息"

    actions = ['export_refund_action']


admin.site.register(Refund, RefundAdmin)


class FreeSampleAdmin(admin.ModelAdmin):
    list_display = ('outer_id', 'name', 'expiry', 'stock')

    search_fields = ['outer_id', 'name']


admin.site.register(FreeSample, FreeSampleAdmin)


class SampleOrderChangeList(ChangeList):
    def get_queryset(self, request):

        # 如果查询条件中含有邀请码
        search_q = request.GET.get('q', '').strip()
        if search_q.isdigit() and len(search_q) in (6, 7, 8):
            return SampleOrder.objects.filter(vipcode=search_q)

        if re.compile('^[\w-]{24,64}$').match(search_q):
            return SampleOrder.objects.filter(user_openid=search_q)

        if re.compile('^[\w]{11}$').match(search_q):
            wxusers = WeiXinUser.objects.filter(mobile=search_q)
            if wxusers.count() > 0:
                return SampleOrder.objects.filter(user_openid=wxusers[0].openid)

        if search_q:
            return SampleOrder.objects.none()

        return super(SampleOrderChangeList, self).get_queryset(request)


class SampleOrderAdmin(ApproxAdmin):
    list_display = ('product_name', 'sku_code', 'user_openid', 'problem_score', 'vipcode', 'created', 'status')
    list_display_links = ('user_openid',)

    list_filter = ('status', 'problem_score')
    search_fields = ['user_openid', 'vipcode']
    list_per_page = 25

    def product_name(self, obj):
        if obj.sample_product:
            return obj.sample_product.name
        return 'NULL'

    product_name.allow_tags = True
    product_name.short_description = u"试用商品名称"

    def sample_link(self, obj):
        return obj.sample_product.name

    sample_link.allow_tags = True
    sample_link.short_description = u"试用商品"

    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        return SampleOrderChangeList


admin.site.register(SampleOrder, SampleOrderAdmin)


class VipCodeChangeList(ChangeList):
    def get_queryset(self, request):

        # 如果查询条件中含有邀请码
        search_q = request.GET.get('q', '').strip()
        if search_q.isdigit() and len(search_q) in (6, 7, 8):
            return VipCode.objects.filter(code=search_q)

        if re.compile('^[\w-]{24,64}$').match(search_q):
            wxusers = WeiXinUser.objects.filter(openid=search_q)
            if wxusers.count() > 0:
                return VipCode.objects.filter(owner_openid=wxusers[0])

        if re.compile('^[\w]{11}$').match(search_q):
            wxusers = WeiXinUser.objects.filter(mobile=search_q)
            if wxusers.count() > 0:
                return VipCode.objects.filter(owner_openid=wxusers[0])

        if search_q:
            return VipCode.objects.none()

        return super(VipCodeChangeList, self).get_queryset(request)


class VipCodeAdmin(ApproxAdmin):
    list_display = ('owner_openid', 'code', 'expiry', 'code_type',
                    'code_rule', 'max_usage', 'usage_count', 'created')

    search_fields = ['owner_openid__openid', 'code']
    list_per_page = 25
    # --------设置页面布局----------------
    fieldsets = ((u'邀请码信息:', {
        'classes': ('expand',),
        'fields': (('code', 'expiry')
                   , ('code_type', 'code_rule')
                   , ('max_usage', 'usage_count')
                   )
    }),
                 )

    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        return VipCodeChangeList


admin.site.register(VipCode, VipCodeAdmin)


class SampleSkuAdmin(admin.ModelAdmin):
    list_display = ('sample_product', 'sku_code', 'sku_name')

    search_fields = ['sku_code', 'sku_name']


admin.site.register(SampleSku, SampleSkuAdmin)


class CouponAdmin(admin.ModelAdmin):
    list_display = ('description', 'coupon_url', 'face_value', 'expiry', 'created')


admin.site.register(Coupon, CouponAdmin)


class CouponClickAdmin(admin.ModelAdmin):
    list_display = ('coupon', 'wx_user', 'vipcode', 'created')
    search_fields = ['wx_user__openid', 'vipcode']


admin.site.register(CouponClick, CouponClickAdmin)


class SurveyAdmin(admin.ModelAdmin):
    list_display = ('selection', 'wx_user', 'created')
    search_fields = ['wx_user__openid']
    list_filter = ('selection',)


admin.site.register(Survey, SurveyAdmin)


class SampleChooseAdmin(admin.ModelAdmin):
    list_display = ('user_openid', 'vipcode', 'selection', 'created')
    search_fields = ['user_openid', 'vipcode', 'mobile']
    list_filter = ('selection',)


admin.site.register(SampleChoose, SampleChooseAdmin)


class WeixinUserScoreAdmin(admin.ModelAdmin):
    list_display = ('user_openid', 'user_score', 'expiring_score', 'created')
    search_fields = ['user_openid', ]


admin.site.register(WeixinUserScore, WeixinUserScoreAdmin)


class WeixinScoreItemAdmin(admin.ModelAdmin):
    list_display = ('user_openid', 'score', 'score_type', 'expired_at', 'created', 'memo')
    search_fields = ['user_openid', 'memo']
    list_filter = ('score_type', ('created', DateFieldListFilter))


admin.site.register(WeixinScoreItem, WeixinScoreItemAdmin)


class WeixinScoreBuyAdmin(admin.ModelAdmin):
    list_display = ('user_openid', 'buy_score', 'created', 'batch')
    search_fields = ['user_openid']
    list_filter = ('batch',)


admin.site.register(WeixinScoreBuy, WeixinScoreBuyAdmin)


class WeixinClickScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'description', 'redirect_link', 'score', 'expiry', 'created')
    search_fields = ['description', 'redirect_link']
    list_filter = ('score',)


admin.site.register(WeixinClickScore, WeixinClickScoreAdmin)


class WeixinClickScoreRecordAdmin(admin.ModelAdmin):
    list_display = ('user_openid', 'click_score_id', 'score', 'created')
    search_fields = ['user_openid']
    list_filter = ('score',)


admin.site.register(WeixinClickScoreRecord, WeixinClickScoreRecordAdmin)


class WeixinFansAdmin(admin.ModelAdmin):
    list_display = ('openid', 'app_key', 'unionid', 'subscribe', 'subscribe_time', 'unsubscribe_time', 'extras')
    search_fields = ['openid', 'unionid']
    list_filter = ('app_key', 'subscribe', ('subscribe_time', DateFieldListFilter),)


admin.site.register(WeixinFans, WeixinFansAdmin)


class WeixinQRcodeTempalteAdmin(admin.ModelAdmin):
    list_display = ('params', 'preview_display', 'status')

    def preview_display(self, obj):
        html = u'<a href="%s"><img src="%s" style="width:120px;"></a>' % (obj.preview_url, obj.preview_url)
        return html

    preview_display.allow_tags = True

admin.site.register(WeixinQRcodeTemplate, WeixinQRcodeTempalteAdmin)
