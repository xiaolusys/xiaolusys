# coding=utf-8
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from django.views.decorators.csrf import csrf_exempt
from .models import XiaoluMama, CarryLog
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
import datetime
from flashsale.clickcount.models import ClickCount
from flashsale.clickrebeta.models import StatisticsShoppingByDay


def referal_From(mobile):
    # 找推荐来的代理
    referals = XiaoluMama.objects.filter(referal_from=mobile, agencylevel=2, charge_status=XiaoluMama.CHARGED)
    return referals


def click_Count(xlmm, left, right):
    # 找点击
    clickcounts = ClickCount.objects.filter(linkid=xlmm, date__gte=left, date__lte=right)
    return clickcounts


def order_Count(xlmm, left, right):
    # 找订单
    right = right + datetime.timedelta(days=1)
    order_counts = StatisticsShoppingByDay.objects.filter(linkid=xlmm, tongjidate__gte=left, tongjidate__lte=right)
    return order_counts


def carry_Log(xlmm, left, right, log_type, status=CarryLog.CONFIRMED):
    carrylogs = CarryLog.objects.filter(xlmm=xlmm, log_type=log_type, carry_date__gte=left, carry_date__lte=right)
    result = carrylogs.filter(status=status)
    sum_value = result.aggregate(total_value=Sum('value')).get('total_value') or 0  # 添加求和函数
    return sum_value / 100.0


def carry_Log_By_date(left, right, xlmm):
    carrylogs = CarryLog.objects.filter(xlmm=xlmm, carry_date__gte=left, carry_date__lte=right)
    # 确认状态
    carrry_in = carrylogs.filter(carry_type=CarryLog.CARRY_IN, status=CarryLog.CONFIRMED)  # 确认收入
    carrry_out = carrylogs.filter(carry_type=CarryLog.CARRY_OUT, status=CarryLog.CONFIRMED)  # 确认支出
    sum_value_in = carrry_in.aggregate(total_value=Sum('value')).get('total_value') or 0
    sum_value_out = carrry_out.aggregate(total_value=Sum('value')).get('total_value') or 0
    # 挂起状态
    carrry_in_pending = carrylogs.filter(xlmm=xlmm, carry_type=CarryLog.CARRY_IN, status=CarryLog.PENDING)  # 待确认收入
    carrry_out_pending = carrylogs.filter(xlmm=xlmm, carry_type=CarryLog.CARRY_OUT, status=CarryLog.PENDING)  # 待确认支出
    sum_value_in_pending = carrry_in_pending.aggregate(total_value=Sum('value')).get('total_value') or 0
    sum_value_out_pending = carrry_out_pending.aggregate(total_value=Sum('value')).get('total_value') or 0
    carry_log_all_sum = [sum_value_in / 100.0, sum_value_out / 100.0, sum_value_in_pending / 100.0,
                         sum_value_out_pending / 100.0]

    # (ORDER_REBETA,u'订单返利'),
    # (ORDER_BUY,u'消费支出'),
    # (REFUND_RETURN,u'退款返现'),
    # (CLICK_REBETA,u'点击兑现'),
    # (CASH_OUT,u'钱包提现'),
    # (DEPOSIT,u'押金'),
    # (THOUSAND_REBETA,u'千元提成'),
    # (AGENCY_SUBSIDY,u'代理补贴'),
    # (MAMA_RECRUIT,u'招募奖金'),
    # (ORDER_RED_PAC,u'订单红包')
    sum_order_reb = carry_Log(xlmm, left, right, log_type=CarryLog.ORDER_REBETA)  # 确定的记录
    sum_order_buy = carry_Log(xlmm, left, right, log_type=CarryLog.ORDER_BUY)  # 确定的记录
    sum_refund = carry_Log(xlmm, left, right, log_type=CarryLog.REFUND_RETURN)  # 确定的记录
    sum_click = carry_Log(xlmm, left, right, log_type=CarryLog.CLICK_REBETA)  # 确定的记录
    sum_cash = carry_Log(xlmm, left, right, log_type=CarryLog.CASH_OUT)  # 确定的记录

    sum_deposit = carry_Log(xlmm, left, right, log_type=CarryLog.DEPOSIT)  # 确定的记录
    sum_thound = carry_Log(xlmm, left, right, log_type=CarryLog.THOUSAND_REBETA)  # 确定的记录
    sum_agency = carry_Log(xlmm, left, right, log_type=CarryLog.AGENCY_SUBSIDY)  # 确定的记录
    sum_mama_rec = carry_Log(xlmm, left, right, log_type=CarryLog.MAMA_RECRUIT)  # 确定的记录
    sum_red_pac = carry_Log(xlmm, left, right, log_type=CarryLog.ORDER_RED_PAC)  # 确定的记录

    sum_order_rebp_ending = carry_Log(xlmm, left, right, log_type=CarryLog.ORDER_REBETA, status=CarryLog.PENDING)
    sum_click_pending = carry_Log(xlmm, left, right, log_type=CarryLog.CLICK_REBETA, status=CarryLog.PENDING)

    sum_thound_pending = carry_Log(xlmm, left, right, log_type=CarryLog.THOUSAND_REBETA, status=CarryLog.PENDING)
    sum_agency_pending = carry_Log(xlmm, left, right, log_type=CarryLog.AGENCY_SUBSIDY, status=CarryLog.PENDING)
    sum_mama_rec_pending = carry_Log(xlmm, left, right, log_type=CarryLog.MAMA_RECRUIT, status=CarryLog.PENDING)
    sum_red_pac_pending = carry_Log(xlmm, left, right, log_type=CarryLog.ORDER_RED_PAC, status=CarryLog.PENDING)

    sum_detail_confirm = [sum_order_reb, sum_order_buy, sum_refund, sum_click, sum_cash, sum_deposit, sum_thound,
                          sum_agency, sum_mama_rec, sum_red_pac]
    sum_detail_pending = [sum_order_rebp_ending, sum_click_pending,
                          sum_thound_pending, sum_agency_pending, sum_mama_rec_pending, sum_red_pac_pending]

    return carry_log_all_sum, sum_detail_confirm, sum_detail_pending


@csrf_exempt
def all_Show(request):
    content = request.GET
    today = datetime.datetime.today()
    left = content.get('date_from') or ''
    right = content.get('date_to') or ''
    xlmm = content.get('xlmm') or 0
    if left is '' or right is '':
        right_date = today.date()
    else:
        year, month, day = right.split('-')
        right_date = datetime.date(int(year), int(month), int(day))
    xlmm = int(xlmm)
    try:
        xlmama = XiaoluMama.objects.get(id=xlmm)
        charge_time = xlmama.charge_time
        left_date = charge_time
    except:
        charge_time = datetime.date(2015, 4, 15)
        left_date = charge_time

    if right and xlmm:
        carry_log_all_sum, sum_detail_confirm, sum_detail_pending = carry_Log_By_date(left_date, right_date, xlmm)
        clickcounts = click_Count(xlmm, left_date, right_date)  # 点击状况
        order_counts = order_Count(xlmm, left_date, right_date)  # 订单状况
        xlmms = XiaoluMama.objects.filter(id=xlmm)

        allcarrylogs = CarryLog.objects.filter(xlmm=xlmm, carry_date__gte=left, carry_date__lte=right)
        if xlmms.exists():
            referals = referal_From(xlmms[0].mobile)  # 推荐代理状况

        return render_to_response("mama_data_search/mama_data_search.html",
                                  {"xlmms": xlmms, "clickcounts": clickcounts, "carry_log_all_sum": carry_log_all_sum,
                                   "order_counts": order_counts, "referals": referals, "allcarrylogs": allcarrylogs,
                                   "xlmm": xlmm, "charge_time": charge_time.strftime("%Y-%m-%d"),
                                   "today": today.strftime("%Y-%m-%d")
                                      , "sum_detail_pending": sum_detail_pending,
                                   "sum_detail_confirm": sum_detail_confirm},
                                  context_instance=RequestContext(request))
    if xlmm:
        xlmms = XiaoluMama.objects.filter(id=xlmm)
        if xlmms.exists():
            referals = referal_From(xlmms[0].mobile)  # 推荐代理状况
            return render_to_response("mama_data_search/mama_data_search.html",
                                      {"xlmms": xlmms, "referals": referals, "xlmm": xlmm,
                                       "charge_time": charge_time.strftime("%Y-%m-%d"),
                                       "today": today.strftime("%Y-%m-%d")},
                                      context_instance=RequestContext(request))

    else:
        return render_to_response("mama_data_search/mama_data_search.html",
                                  {"xlmm": xlmm, "charge_time": charge_time.strftime("%Y-%m-%d"),
                                   "today": today.strftime("%Y-%m-%d")}, context_instance=RequestContext(request))
