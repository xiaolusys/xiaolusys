# -*- coding:utf-8 -*-
import datetime
import json
import logging
import re
import urllib
import urlparse

from celery import chain
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render
from django.template import RequestContext
from django.views.generic import View
from flashsale.xiaolumm.models.models_advertis import XlmmAdvertis
from rest_framework import generics
from rest_framework.renderers import JSONRenderer

from common.modelutils import update_model_fields
from core.options import log_action, CHANGE
from core.weixin.mixins import WeixinAuthMixin
from flashsale.clickcount import tasks as ctasks
from flashsale.clickcount.models import Clicks, ClickCount
from flashsale.clickrebeta.models import StatisticsShoppingByDay, StatisticsShopping
from flashsale.pay.models import SaleTrade, Customer, SaleRefund, Envelop, SaleOrder
from shopapp.weixin.models import WeiXinUser
from shopapp.weixin.options import get_unionid_by_openid
from shopapp.weixin.views import valid_openid
from flashsale.xiaolumm.models import XiaoluMama, CashOut, CarryLog
from flashsale.xiaolumm.serializers import CashOutSerializer, CarryLogSerializer

logger = logging.getLogger(__name__)
json_logger = logging.getLogger('service.xiaolumama')

SHOPURL = "http://mp.weixin.qq.com/bizmall/mallshelf?id=&t=mall/list&biz=MzA5NTI1NjYyNg==&shelf_id=2&showwxpaytitle=1#wechat_redirect"
WEB_SHARE_URL = "{site_url}/mall/?mm_linkid={mm_linkid}&ufrom={ufrom}"


# SHOPURL = "http://m.xiaolumeimei.com/mm/plist/"

def landing(request):
    return render(
        request,
        "mama_landing.html",
    )


class WeixinAuthCheckView(WeixinAuthMixin, View):
    """ 微信授权参数检查 """

    def get(self, request):
        self.set_appid_and_secret(settings.WXPAY_APPID, settings.WXPAY_SECRET)
        openid, unionid = self.get_openid_and_unionid(request)
        if not valid_openid(openid):
            redirect_url = self.get_snsuserinfo_redirct_url(request)
            return redirect(redirect_url)

        xlmm = None
        wxuser = None
        xlmm_qs = XiaoluMama.objects.filter(openid=unionid)
        if xlmm_qs.exists():
            xlmm = xlmm_qs[0]
        wxuser_qs = WeiXinUser.objects.filter(openid=openid)
        if wxuser_qs.exists():
            wxuser = wxuser_qs[0]

        return render(
            request,
            'wxauth_checkview.html',
            {'openid': openid,
             'unionid': unionid,
             'xlmm': xlmm,
             'wxuser': wxuser,
             },
        )


def get_xlmm_cash_iters(xlmm, cash_outable=False):
    cash = xlmm.cash / 100.0
    clog_outs = CarryLog.objects.filter(xlmm=xlmm.id,
                                        log_type=CarryLog.ORDER_BUY,
                                        carry_type=CarryLog.CARRY_OUT,
                                        status=CarryLog.CONFIRMED)
    consume_value = (clog_outs.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0

    clog_refunds = CarryLog.objects.filter(xlmm=xlmm.id,
                                           log_type=CarryLog.REFUND_RETURN,
                                           carry_type=CarryLog.CARRY_IN,
                                           status=CarryLog.CONFIRMED)
    refund_value = (clog_refunds.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0

    payment = consume_value - refund_value
    x_choice = cash_outable and xlmm.get_Mama_Deposite() or xlmm.get_Mama_Deposite_Amount()

    mony_without_pay = cash + payment  # 从未消费情况下的金额
    leave_cash_out = mony_without_pay - x_choice - xlmm.lowest_uncoushout  # 减去代理的最低不可提现金额(充值) = 可提现金额
    could_cash_out = cash
    if leave_cash_out < cash:
        could_cash_out = leave_cash_out

    if could_cash_out < 0:
        could_cash_out = 0
    return (cash, payment, could_cash_out)


class CashoutView(WeixinAuthMixin, View):
    def get(self, request):

        openid, unionid = self.get_openid_and_unionid(request)
        if not valid_openid(openid) or not valid_openid(unionid):
            redirect_url = self.get_snsuserinfo_redirct_url(request)
            return redirect(redirect_url)

        xlmm = XiaoluMama.objects.get(openid=unionid)
        referal_list = XiaoluMama.objects.filter(referal_from=xlmm.mobile, status=XiaoluMama.EFFECT)
        cashout_objs = CashOut.objects.filter(xlmm=xlmm.pk)

        # day_to   = datetime.datetime.now()
        #         day_from = day_to - datetime.timedelta(days=30)
        # 点击数
        clickcounts = ClickCount.objects.filter(linkid=xlmm.id)
        click_nums = clickcounts.aggregate(total_count=Sum('valid_num')).get('total_count') or 0

        # 订单数
        shoppings = StatisticsShopping.objects.filter(linkid=xlmm.id)
        shoppings_count = shoppings.count()

        app_cashouts = cashout_objs.filter(status__in=(CashOut.APPROVED, CashOut.COMPLETED)).order_by('created')
        kefu_mobile = '18516655836'
        if app_cashouts.count() == 0 or app_cashouts[0].created > datetime.datetime(2015, 6, 30, 15):
            kefu_mobile = '18516316989'
        cash_outable = (click_nums >= 150 and shoppings_count >= 1) or shoppings_count >= 6
        cash, payment, could_cash_out = get_xlmm_cash_iters(xlmm, cash_outable=cash_outable)
        pending_cashouts = cashout_objs.filter(status=CashOut.PENDING)
        data = {"xlmm": xlmm,
                "cashout": pending_cashouts.count(),
                'kefu_mobile': kefu_mobile,
                "referal_list": referal_list,
                "could_cash_out": int(could_cash_out)}

        response = render(
            request,
            "mama_cashout.html",
            data,
        )
        self.set_cookie_openid_and_unionid(response, openid, unionid)
        return response

    def post(self, request):
        content = request.POST
        openid, unionid = self.get_openid_and_unionid(request)
        if not valid_openid(unionid):
            raise Http404
        could_cash_out = 0
        xlmm = XiaoluMama.objects.filter(openid=unionid)
        if xlmm.count() > 0:
            # 点击数
            clickcounts = ClickCount.objects.filter(linkid=xlmm[0].id)
            click_nums = clickcounts.aggregate(total_count=Sum('valid_num')).get('total_count') or 0
            # 订单数
            shoppings = StatisticsShopping.objects.filter(linkid=xlmm[0].id)
            shoppings_count = shoppings.count()
            cash_outable = click_nums >= 150 or shoppings_count >= 6
            cash, payment, could_cash_out = get_xlmm_cash_iters(xlmm[0], cash_outable=cash_outable)
        v = content.get("v")
        m = re.match(r'^\d+$', v)
        status = {"code": 0, "status": "ok"}
        if m:
            value = int(m.group()) * 100
            could_cash_out_int = int(could_cash_out) * 100
            # 2015-8-28 修改为　只是允许１００　和200　提现
            # if value < 2000 or value > 20000 or value > could_cash_out_int:
            if value not in (10000, 20000) or value > could_cash_out_int:
                status = {"code": 3, "status": "input error"}
            else:
                try:
                    xlmm = XiaoluMama.objects.get(openid=unionid)
                    cash_out = CashOut(xlmm=xlmm.pk,
                                       cash_out_type=CashOut.RED_PACKET,
                                       value=value)
                    cash_out.approve_time = datetime.datetime.now()
                    cash_out.save()
                except:
                    status = {"code": 1, "status": "error"}
        else:
            status = {"code": 2, "status": "input error"}

        return HttpResponse(json.dumps(status), content_type='application/json')


class CashOutList(generics.ListAPIView):
    queryset = CashOut.objects.all().order_by('-created')
    serializer_class = CashOutSerializer
    renderer_classes = (JSONRenderer,)
    filter_fields = ("xlmm",)


class CarryLogList(generics.ListAPIView):
    queryset = CarryLog.objects.order_by('-carry_date')  #
    serializer_class = CarryLogSerializer
    renderer_classes = (JSONRenderer,)
    filter_fields = ("xlmm",)


class MamaStatsView(WeixinAuthMixin, View):
    def get(self, request):
        if True:
            return redirect('/sale/promotion/appdownload/')
        openid, unionid = self.get_openid_and_unionid(request)
        if not valid_openid(openid) or not valid_openid(unionid):
            redirect_url = self.get_snsuserinfo_redirct_url(request)
            return redirect(redirect_url)

        # service = WeixinUserService(settings.WEIXIN_APPID, openId=openid, unionId=unionid)
        # wx_user = service._wx_user

        wx_users = Customer.objects.filter(unionid=unionid, status=Customer.NORMAL)
        if not wx_users.exists():
            return HttpResponse(u'<html><body>你还不是小鹿妈妈,请先<a href="/m/register/">申请</a></body></html>')

        wx_user = wx_users[0]
        target_date = datetime.date.today()
        yesterday = target_date - datetime.timedelta(days=1)
        time_from = datetime.datetime(target_date.year, target_date.month, target_date.day)
        time_to = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)

        mobile = wx_user.mobile
        unionid = unionid or wx_user.unionid
        data = {}
        try:
            referal_num = XiaoluMama.objects.filter(referal_from=mobile, status=XiaoluMama.EFFECT).count()
            xlmm, state = XiaoluMama.objects.get_or_create(openid=unionid)
            if xlmm.mobile != mobile:
                xlmm.mobile = mobile
                xlmm.weikefu = xlmm.weikefu or wx_user.nick
                update_model_fields(xlmm, update_fields=['mobile', 'weikefu'])

            if xlmm.status == XiaoluMama.FROZEN:
                return render(
                    request,
                    "mama_404.html"
                )

            mobile_revised = "%s****%s" % (mobile[:3], mobile[-4:])

            mm_clogs = CarryLog.objects.filter(xlmm=xlmm.id)  # .exclude(log_type=CarryLog.ORDER_RED_PAC)
            pending_value = mm_clogs.filter(status=CarryLog.PENDING).aggregate(total_value=Sum('value')).get(
                'total_value') or 0

            total_income = mm_clogs.filter(carry_type=CarryLog.CARRY_IN, status=CarryLog.CONFIRMED).aggregate(
                total_value=Sum('value')).get('total_value') or 0
            total_pay = mm_clogs.filter(carry_type=CarryLog.CARRY_OUT, status=CarryLog.CONFIRMED).aggregate(
                total_value=Sum('value')).get('total_value') or 0

            yest_income = mm_clogs.filter(carry_type=CarryLog.CARRY_IN, carry_date=yesterday).aggregate(
                total_value=Sum('value')).get('total_value') or 0
            yest_pay = mm_clogs.filter(carry_type=CarryLog.CARRY_OUT, carry_date=yesterday).aggregate(
                total_value=Sum('value')).get('total_value') or 0

            pending_value = pending_value / 100.0
            total_income = total_income / 100.0
            total_pay = total_pay / 100.0
            yest_income = yest_income / 100.0
            yest_pay = yest_pay / 100.0

            abnormal_cash = xlmm.cash_money - (total_income - total_pay)  # 异常金额
            order_num = 0
            order_stat = StatisticsShoppingByDay.objects.filter(linkid=xlmm.pk, tongjidate=target_date)
            if order_stat.count() > 0:
                order_num = order_stat[0].buyercount

            click_list = Clicks.objects.filter(linkid=xlmm.pk, click_time__range=(time_from, time_to), isvalid=True)
            click_num = click_list.values('openid').distinct().count()

            # 设置最高有效最高点击上限
            max_click_count = xlmm.get_Mama_Max_Valid_Clickcount(order_num, day_date=target_date)
            if time_from.date() >= ctasks.CLICK_MAX_LIMIT_DATE:
                click_num = min(max_click_count, click_num)

            referal_mm = 0
            # if xlmm.progress != XiaoluMama.PASS :
            #                 if xlmm.referal_from:
            #                     referal_mamas = XiaoluMama.objects.filter(mobile=xlmm.referal_from)
            #                     if referal_mamas.count() > 0:
            #                         referal_mm = referal_mamas[0].id
            #                 else:
            #                     referal_mm = 1
            try:
                adver = XlmmAdvertis.objects.get(show_people=xlmm.agencylevel, is_valid=True)
                now = datetime.datetime.now()
                if now >= adver.start_time and now <= adver.end_time:
                    adv_cntnt = adver
                else:
                    adv_cntnt = None
            except XlmmAdvertis.DoesNotExist:
                adv_cntnt = None

            data = {"mobile": mobile_revised, "click_num": click_num, "xlmm": xlmm, "advertise": adv_cntnt,
                    'referal_mmid': referal_mm, "order_num": order_num, "pk": xlmm.pk,
                    'pending_value': pending_value, "referal_num": referal_num,
                    'total_income': total_income, 'total_pay': total_pay, 'abnormal_cash': abnormal_cash,
                    'yest_income': yest_income, 'yest_pay': yest_pay}

        except Exception, exc:
            logger.error(exc.message, exc_info=True)

        response = render(
            request,
            "mama_stats.html",
            data,
        )
        self.set_cookie_openid_and_unionid(response, openid, unionid)
        return response


class MamaIncomeDetailView(WeixinAuthMixin, View):
    def get(self, request):
        content = request.GET
        openid, unionid = self.get_openid_and_unionid(request)
        if not valid_openid(openid) or not valid_openid(unionid):
            redirect_url = self.get_snsuserinfo_redirct_url(request)
            return redirect(redirect_url)

        wx_users = Customer.objects.filter(unionid=unionid, status=Customer.NORMAL)
        if not wx_users.exists():
            return HttpResponse(u'<html><body>你还不是小鹿妈妈,请先<a href="/m/register/">申请</a></body></html>')

        wx_user = wx_users[0]
        unionid = unionid or wx_user.unionid
        daystr = content.get("day", None)
        today = datetime.date.today()
        year, month, day = today.year, today.month, today.day

        target_date = today
        if daystr:
            year, month, day = daystr.split('-')
            target_date = datetime.date(int(year), int(month), int(day))
            if target_date > today:
                target_date = today

        time_from = datetime.datetime(target_date.year, target_date.month, target_date.day)
        time_to = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)

        active_start = ctasks.CLICK_ACTIVE_START_TIME.date() == time_from.date()
        prev_day = target_date - datetime.timedelta(days=1)
        next_day = None
        if target_date < today:
            next_day = target_date + datetime.timedelta(days=1)

        data = {}
        try:
            xlmm, state = XiaoluMama.objects.get_or_create(openid=unionid)
            if xlmm.status == XiaoluMama.FROZEN:
                return render(
                    request,
                    "mama_404.html"
                )

            exam_pass = xlmm.exam_Passed()
            order_num = 0
            total_value = 0
            carry = 0
            rebeta_swift = False

            order_list = StatisticsShopping.normal_objects.filter(linkid=xlmm.pk, shoptime__range=(time_from, time_to))
            order_stat = StatisticsShoppingByDay.objects.filter(linkid=xlmm.pk, tongjidate=target_date)
            carry_confirm = False
            # if target_date >= ORDER_RATEUP_START:
            #                 rebeta_swift = True

            if order_stat.count() > 0:
                order_num = order_stat[0].buyercount
                total_value = order_stat[0].orderamountcount / 100.0
                carry = order_stat[0].todayamountcount / 100.0
                carry_confirm = order_stat[0].carry_Confirm()

            click_price = xlmm.get_Mama_Click_Price_By_Day(order_num, day_date=target_date) / 100.0
            futrue_date = datetime.date.today() + datetime.timedelta(days=1)
            futrue_click_price = 0
            if target_date == datetime.date.today():
                futrue_click_price = xlmm.get_Mama_Click_Price_By_Day(0, day_date=futrue_date) / 100.0

            click_num = 0
            click_pay = 0
            ten_click_num = 0
            ten_click_price = click_price + 0.3
            ten_click_pay = 0
            if not active_start:
                click_state = ClickCount.objects.filter(linkid=xlmm.pk, date=target_date)
                if click_state.count() > 0:
                    click_num = click_state[0].valid_num
                else:
                    click_list = Clicks.objects.filter(linkid=xlmm.pk, click_time__range=(time_from, time_to),
                                                       isvalid=True)
                    click_num = click_list.values('openid').distinct().count()

                # 设置最高有效最高点击上限
                max_click_count = xlmm.get_Mama_Max_Valid_Clickcount(order_num, day_date=target_date)
                if time_from.date() >= ctasks.CLICK_MAX_LIMIT_DATE:
                    click_num = min(max_click_count, click_num)

                click_pay = click_price * click_num
            else:
                click_qs = Clicks.objects.filter(linkid=xlmm.pk, isvalid=True)
                click_num = click_qs.filter(click_time__range=(datetime.datetime(2015, 6, 15),
                                                               datetime.datetime(2015, 6, 15, 10, 0, 0))
                                            ).values('openid').distinct().count()

                ten_click_num = click_qs.filter(click_time__range=(datetime.datetime(2015, 6, 15, 10),
                                                                   datetime.datetime(2015, 6, 15, 23, 59, 59))
                                                ).values('openid').distinct().count()

                # 设置最高有效最高点击上限
                max_click_count = xlmm.get_Mama_Max_Valid_Clickcount(order_num, day_date=target_date)
                if time_from.date() >= ctasks.CLICK_MAX_LIMIT_DATE:
                    click_num = min(max_click_count, click_num)
                    ten_click_num = min(max_click_count, ten_click_num)

                click_pay = click_num * click_price
                ten_click_pay = ten_click_num * ten_click_price

            data = {"xlmm": xlmm, "pk": xlmm.pk, 'rebeta_swift': rebeta_swift,
                    "order_num": order_num, "order_list": order_list,
                    "exam_pass": exam_pass, "total_value": total_value,
                    "carry": carry, 'carry_confirm': carry_confirm,
                    "target_date": target_date, "prev_day": prev_day, "next_day": next_day,
                    'active_start': active_start, "click_num": click_num, "futrue_click_price": futrue_click_price,
                    "click_price": click_price, "click_pay": click_pay, "ten_click_num": ten_click_num,
                    "ten_click_price": ten_click_price, "ten_click_pay": ten_click_pay}

        except Exception, exc:
            logger.error(exc.message, exc_info=True)

        response = render(
            request,
            "mama_income.html",
            data,
        )
        self.set_cookie_openid_and_unionid(response, openid, unionid)
        return response


class StatsView(View):
    def getUserName(self, uid):
        try:
            return User.objects.get(pk=uid).username
        except:
            return 'none'

    def get(self, request):
        content = request.GET
        daystr = content.get("day", None)
        today = datetime.date.today()
        year, month, day = today.year, today.month, today.day

        target_date = today
        if daystr:
            year, month, day = daystr.split('-')
            target_date = datetime.date(int(year), int(month), int(day))
            if target_date > today:
                target_date = today

        time_from = datetime.datetime(target_date.year, target_date.month, target_date.day)
        time_to = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)

        prev_day = target_date - datetime.timedelta(days=1)
        next_day = None
        if target_date < today:
            next_day = target_date + datetime.timedelta(days=1)

        pk = content.get('pk', '6')
        mama_list = XiaoluMama.objects.filter(manager=pk)
        mama_managers = XiaoluMama.objects.values('manager').distinct()
        manager_ids = [m.get('manager') for m in mama_managers if m]
        managers = User.objects.filter(id__in=manager_ids)
        data = []

        for mama in mama_list:
            buyer_num = 0
            order_num = 0
            click_num = 0
            user_num = 0
            weikefu = mama.weikefu
            mobile = mama.mobile
            agencylevel = mama.agencylevel
            username = self.getUserName(mama.manager)

            day_stats = StatisticsShoppingByDay.objects.filter(linkid=mama.pk, tongjidate=target_date)
            if day_stats.count() > 0:
                buyer_num = day_stats[0].buyercount
                order_num = day_stats[0].ordernumcount

            click_counts = ClickCount.objects.filter(linkid=mama.pk, date=target_date)
            if click_counts.count() > 0:
                click_num = click_counts[0].click_num
                user_num = click_counts[0].user_num
            else:
                click_list = Clicks.objects.filter(linkid=mama.pk, click_time__range=(time_from, time_to))
                click_num = click_list.count()
                openid_list = click_list.values('openid').distinct()
                user_num = openid_list.count()

            data_entry = {"mobile": mobile[-4:], "weikefu": weikefu,
                          "agencylevel": agencylevel, 'username': username,
                          "click_num": click_num, "user_num": user_num,
                          "buyer_num": buyer_num, "order_num": order_num}
            data.append(data_entry)

        return render(
            request,
            "stats.html",
            {'pk': int(pk), "data": data, "managers": managers, "prev_day": prev_day,
             "target_date": target_date, "next_day": next_day},
        )


def get_share_url(next_page=None, mm_linkid=None, ufrom=None):
    """ 获取分享链接 """
    if next_page:
        next_page = urllib.unquote(next_page)
        url_ps = urlparse.urlparse(next_page)
        query_dict = dict(urlparse.parse_qsl(url_ps.query))
        if mm_linkid:
            query_dict.update(mm_linkid=mm_linkid)
        if ufrom:
            query_dict.update(ufrom=ufrom)
        query_string = urllib.urlencode(query_dict)
        fragment = url_ps.fragment
        share_url = urlparse.urljoin(settings.M_SITE_URL,
                                     '{path}?{query}#{fragement}'.format(
                                         path=url_ps.path,
                                         query=query_string,
                                         fragement=fragment
                                     ))
    else:
        share_url = WEB_SHARE_URL.format(site_url=settings.M_SITE_URL,
                                         mm_linkid=mm_linkid, ufrom=ufrom)
    return share_url


class ClickLogView(WeixinAuthMixin, View):
    """ 微信授权参数检查 """

    def get(self, request, linkid):
        from django_statsd.clients import statsd

        statsd.incr('xiaolumm.weixin_click')
        content = request.GET
        next_page = content.get('next', None)
        # print 'next_page:', next_page
        # logger.error('next_page %s-path:%s' % (next_page, content))
        click_time = datetime.datetime.now()
        json_logger.info({
            'stype': 'click', 'mm_linkid': linkid, 'click_time': click_time,
            'http_referal': request.META.get('HTTP_REFERER'),
            'http_agent': request.META.get('HTTP_USER_AGENT')
        })
        if not self.is_from_weixin(request):
            share_url = get_share_url(next_page=next_page, mm_linkid=linkid, ufrom='web')
            response = redirect(share_url)
            response.set_cookie('mm_linkid', linkid, max_age=86400)
            return response

        self.set_appid_and_secret(settings.WXPAY_APPID, settings.WXPAY_SECRET)
        openid, unionid = self.get_openid_and_unionid(request)
        if not valid_openid(openid):
            redirect_url = self.get_wxauth_redirct_url(request)
            return redirect(redirect_url)

        json_logger.info({
            'stype': 'auth_click', 'mm_linkid': linkid, 'click_time': click_time,
            'openid': openid, 'unionid': unionid,
            'http_referal': request.META.get('HTTP_REFERER'),
            'http_agent': request.META.get('HTTP_USER_AGENT')
        })
        chain(ctasks.task_Create_Click_Record.s(linkid, openid, unionid, click_time, settings.WXPAY_APPID),
              ctasks.task_Update_User_Click.s())()

        if not valid_openid(unionid):
            unionid = get_unionid_by_openid(openid, settings.WXPAY_APPID)
        xlmms = XiaoluMama.objects.filter(openid=unionid, status=XiaoluMama.EFFECT, charge_status=XiaoluMama.CHARGED)
        mm_linkid = xlmms.exists() and xlmms[0].id or linkid

        share_url = get_share_url(next_page=next_page, mm_linkid=mm_linkid, ufrom='wx')
        response = redirect(share_url)
        self.set_cookie_openid_and_unionid(response, openid, unionid)
        response.set_cookie('mm_linkid', linkid, max_age=86400)
        return response


class ClickChannelLogView(WeixinAuthMixin, View):
    """ 微信授权参数检查 """

    def get(self, request, linkid):

        if not self.is_from_weixin(request):
            share_url = WEB_SHARE_URL.format(site_url=settings.M_SITE_URL, mm_linkid=linkid, ufrom='web')
            return redirect(share_url)
        self.set_appid_and_secret(settings.WXPAY_APPID, settings.WXPAY_SECRET)
        openid, unionid = self.get_openid_and_unionid(request)
        if not valid_openid(openid):
            redirect_url = self.get_wxauth_redirct_url(request)
            return redirect(redirect_url)
        click_time = datetime.datetime.now()
        chain(ctasks.task_Create_Click_Record.s(linkid, openid, unionid, click_time, settings.WXPAY_APPID),
              ctasks.task_Update_User_Click.s())()
        if not valid_openid(unionid):
            unionid = get_unionid_by_openid(openid, settings.WXPAY_APPID)
        xlmms = XiaoluMama.objects.filter(openid=unionid)
        if xlmms.exists():
            share_url = WEB_SHARE_URL.format(site_url=settings.M_SITE_URL, mm_linkid=xlmms[0].id, ufrom='wx')
        else:
            share_url = settings.M_SITE_URL
        response = redirect(share_url)
        self.set_cookie_openid_and_unionid(response, openid, unionid)
        return response


from django.shortcuts import get_object_or_404
from django.forms import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder


def chargeWXUser(request, pk):
    result = {}
    employee = request.user

    xiaolumm = get_object_or_404(XiaoluMama, pk=pk)

    charged = XiaoluMama.objects.charge(xiaolumm, employee)
    if not charged:
        result = {'code': 1, 'error_response': u'已经被接管'}

    if charged:
        result = {'success': True}

        log_action(request.user.id, xiaolumm, CHANGE, u'接管用户')

    return HttpResponse(json.dumps(result), content_type='application/json')


class XiaoluMamaModelView(View):
    """ 微信接收消息接口 """

    def post(self, request, pk):
        content = request.POST
        user_group_id = content.get('user_group_id')

        xlmm = get_object_or_404(XiaoluMama, pk=pk)
        xlmm.user_group_id = user_group_id
        xlmm.save()

        user_dict = {'code': 0, 'response_content':
            model_to_dict(xlmm, fields=['id', 'user_group', 'charge_status'])}

        return HttpResponse(json.dumps(user_dict, cls=DjangoJSONEncoder),
                            content_type="application/json")


from django.views.decorators.csrf import csrf_exempt

from django.db import transaction
from django.conf import settings
from shopapp.weixin.models import WeixinUnionID
from flashsale.xiaolumm.models.models_fortune import MamaFortune

from django.db.models import Sum


def manage_Summar(date_time):
    data = []
    xiaolumamas = XiaoluMama.objects.exclude(charge_status=XiaoluMama.UNCHARGE, manager=0).filter \
        (agencylevel__gte=XiaoluMama.VIP_LEVEL).values('manager').distinct()
    date = date_time.date()
    for xlmm_manager in xiaolumamas:
        xiaolumama_manager2 = xlmm_manager['manager']
        clickcounts = ClickCount.objects.filter(username=xiaolumama_manager2, date=date,
                                                agencylevel__gte=XiaoluMama.VIP_LEVEL)  # 当天的该管理员的所有代理的点击
        xlmms = XiaoluMama.objects.filter(agencylevel__gte=XiaoluMama.VIP_LEVEL, manager=xiaolumama_manager2,
                                          charge_status=XiaoluMama.CHARGED,
                                          charge_time__lt=date_time)  # 该管理员在对应日期之前接管的代理
        xlmm_num = xlmms.count()  # 这个管理员下面的妈妈数量

        sum_valied_num = clickcounts.aggregate(total_valied_num=Sum('valid_num')).get('total_valied_num') or 0  # 总有效点击
        sum_click_num = clickcounts.aggregate(total_click_num=Sum('click_num')).get('total_click_num') or 0  # 总点击
        sum_user_num = clickcounts.aggregate(total_user_num=Sum('user_num')).get('total_user_num') or 0  # 总点击人数

        active_num = clickcounts.filter(user_num__gt=4).count()  # 点击人数大于4即纳入活跃代理
        activity_func = lambda acti, total: 0 if total == 0 else round(float(acti) / total,
                                                                       3)  # 活跃度 点击人数大于4的妈妈个数／总的妈妈个数
        activity = activity_func(active_num, xlmm_num)

        xlmm_lit = [val.id for val in xlmms]  # 代理id列表

        shoppings = StatisticsShoppingByDay.objects.filter(linkid__in=xlmm_lit, tongjidate=date)  #
        sum_buyercount = shoppings.aggregate(total_shoppings=Sum('buyercount')).get('total_shoppings') or 0  # 购买人数
        sum_ordernumcount = shoppings.aggregate(total_ordernumcount=Sum('ordernumcount')).get(
            'total_ordernumcount') or 0  # 订单数量
        try:
            username = User.objects.get(id=xiaolumama_manager2).username
        except:
            username = 'error.manager'
        conve_func = lambda buys, useers: 0 if useers == 0 else round(float(buys) / useers, 3)
        conversion_rate = conve_func(sum_buyercount, sum_user_num)  # 转化率等于 购买人数 除以 点击数

        data_entry = {"username": username, "sum_ordernumcount": sum_ordernumcount, "sum_buyercount": sum_buyercount,
                      "uv_summary": sum_user_num, "pv_summary": sum_click_num, "conversion_rate": conversion_rate,
                      "xlmm_num": xlmm_num, "activity": activity, 'sum_click_valid': sum_valied_num}
        data.append(data_entry)
    return data


@csrf_exempt
def stats_summary(request):
    # 根据日期查看每个管理人员 所管理的所有代理的点击情况和转化情况
    content = request.GET
    daystr = content.get("day", None)
    today = datetime.date.today()
    target_date = today
    if daystr:
        year, month, day = daystr.split('-')
        target_date = datetime.date(int(year), int(month), int(day))
        if target_date >= today:
            target_date = today
    date_time = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)
    date = date_time.date()
    prev_day = target_date - datetime.timedelta(days=1)
    next_day = None
    if target_date < today:
        next_day = target_date + datetime.timedelta(days=1)
    data = manage_Summar(date_time)
    return render(
        request,
        "stats_summary.html",
        {"data": data, "prev_day": prev_day,
         "target_date": target_date, "next_day": next_day},
    )


from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response


class CashOutVerify(APIView):
    """
    补发遗漏的优惠券
    参数：优惠券模板
    用户：客户信息(用户手机号，或者用户id)
    """
    queryset = CashOut.objects.all()
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions, permissions.IsAdminUser)

    def get(self, request):
        return Response({})

    @transaction.atomic
    def post(self, request):
        print request.POST
        action = request.POST.get('action')
        cash_out_id = request.POST.get('cash_out_id')
        if not cash_out_id and action:
            return Response({'code': 1, 'info': '参数错误!'})
        cashout = self.queryset.filter(id=cash_out_id).first()
        if cashout.status != CashOut.PENDING:
            return Response({'code': 2, 'info': '审核状态错误！'})

        if action == CashOut.REJECTED:
            cashout.status = CashOut.REJECTED
            cashout.save()
            return Response({'code': 0, 'info': '拒绝成功'})
        if action == CashOut.APPROVED:
            mama_id = cashout.xlmm
            fortune = MamaFortune.objects.get(mama_id=mama_id)
            pre_cash = fortune.cash_num_display() + (cashout.value * 0.01)
            xiaolumama = XiaoluMama.objects.get(id=mama_id)  # object.get(id=mama_id)

            if not xiaolumama.is_cashoutable():
                return Response({'code': 3, 'info': '该妈妈不予提现!'})
            if pre_cash * 100 >= cashout.value:
                cashout.status = CashOut.APPROVED
                cashout.approve_time = datetime.datetime.now()
                cashout.save()
                logger.warn('cashout save approved: cash_d:%s mama_id:'
                            '%s pre_cash:%s cashout_value:%s' % (cash_out_id, mama_id, pre_cash, cashout.value))
                today_dt = datetime.date.today()
                CarryLog.objects.get_or_create(xlmm=mama_id,
                                               order_num=cash_out_id,
                                               log_type=CarryLog.CASH_OUT,
                                               value=cashout.value,
                                               carry_date=today_dt,
                                               carry_type=CarryLog.CARRY_OUT,
                                               status=CarryLog.CONFIRMED)
                wx_union = WeixinUnionID.objects.get(app_key=settings.WXPAY_APPID, unionid=xiaolumama.openid)
                mama_memo = u"小鹿妈妈编号:{0},提现前:{1}"
                Envelop.objects.get_or_create(referal_id=cashout.id,
                                              amount=cashout.value,
                                              recipient=wx_union.openid,
                                              platform=Envelop.WXPUB,
                                              subject=Envelop.CASHOUT,
                                              status=Envelop.WAIT_SEND,
                                              receiver=mama_id,
                                              body=u'一份耕耘，一份收获，谢谢你的努力！',
                                              description=mama_memo.format(str(mama_id), pre_cash))
                log_action(request.user.id, cashout, CHANGE, u'提现审核通过')
                return Response({'code': 0, 'info': '审核成功'})
            return Response({'code': 4, 'info': '金额不足'})
        return Response({'code': 5, "info": '操作错误!'})
