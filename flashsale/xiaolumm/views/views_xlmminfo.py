# coding=utf-8
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Sum
from django.views.generic import View
from django.shortcuts import HttpResponse
from django.shortcuts import get_object_or_404

from flashsale.clickcount.models import ClickCount
from flashsale.clickrebeta.models import StatisticsShopping
from flashsale.xiaolumm.models import XiaoluMama, CarryLog
from common.modelutils import update_model_fields
from core.options import log_action, CHANGE

import datetime
import logging
import json

logger = logging.getLogger('django.request')


def referal_From(mobile):
    # 找推荐来的代理
    referals = XiaoluMama.objects.filter(referal_from=mobile, agencylevel__gte=XiaoluMama.VIP_LEVEL,
                                         charge_status=XiaoluMama.CHARGED)
    return referals


def click_Count(xlmm, left, right):
    # 找点击
    clickcounts = ClickCount.objects.filter(linkid=xlmm, date__gte=left, date__lte=right)
    return clickcounts


def order_Count(xlmm, left, right):
    # 找订单
    right = right + datetime.timedelta(days=1)
    order_counts = StatisticsShopping.objects.filter(linkid=xlmm, shoptime__gte=left, shoptime__lte=right).exclude(
        status=StatisticsShopping.REFUNDED)
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
    sum_recharge = carry_Log(xlmm, left, right, log_type=CarryLog.RECHARGE)  # 确定的记录

    sum_order_rebp_ending = carry_Log(xlmm, left, right, log_type=CarryLog.ORDER_REBETA, status=CarryLog.PENDING)
    sum_click_pending = carry_Log(xlmm, left, right, log_type=CarryLog.CLICK_REBETA, status=CarryLog.PENDING)

    sum_thound_pending = carry_Log(xlmm, left, right, log_type=CarryLog.THOUSAND_REBETA, status=CarryLog.PENDING)
    sum_agency_pending = carry_Log(xlmm, left, right, log_type=CarryLog.AGENCY_SUBSIDY, status=CarryLog.PENDING)
    sum_mama_rec_pending = carry_Log(xlmm, left, right, log_type=CarryLog.MAMA_RECRUIT, status=CarryLog.PENDING)
    sum_red_pac_pending = carry_Log(xlmm, left, right, log_type=CarryLog.ORDER_RED_PAC, status=CarryLog.PENDING)

    sum_detail_confirm = [sum_order_reb, sum_order_buy, sum_refund, sum_click, sum_cash, sum_deposit, sum_thound,
                          sum_agency, sum_mama_rec, sum_red_pac, sum_recharge]
    sum_detail_pending = [sum_order_rebp_ending, sum_click_pending,
                          sum_thound_pending, sum_agency_pending, sum_mama_rec_pending, sum_red_pac_pending]

    return carry_log_all_sum, sum_detail_confirm, sum_detail_pending


class XlmmInfo(View):
    template = 'xlmm_info/xlmm_info.html'

    def handler_date(self, request):
        content = request.GET
        left = content.get('date_from', None)
        right = content.get('date_to', None)
        if right is None or left is None:
            right = datetime.date.today()
            left = right - datetime.timedelta(days=15)
            return left, right
        year, month, day = map(int, right.split('-'))
        right_date = datetime.date(year, month, day)
        year, month, day = map(int, left.split('-'))
        left_date = datetime.date(year, month, day)
        return left_date, right_date

    def calcu_data(self, request):
        content = request.GET
        left_date, right_date = self.handler_date(request)
        xlmm = map(int, [content.get('id', 0)])[0]
        carry_log_all_sum, sum_detail_confirm, sum_detail_pending = carry_Log_By_date(left_date, right_date, xlmm)
        clickcounts = click_Count(xlmm, left_date, right_date)  # 点击状况
        total_clicks = clickcounts.aggregate(clis=Sum('valid_num')).get('clis') or 0  # 点击总数
        order_counts = order_Count(xlmm, left_date, right_date)  # 订单状况
        total_orders = order_counts.count()  # 订单总数(不包含取消的)

        xlmm_obj = XiaoluMama.objects.get(id=xlmm)

        allcarrylogs = CarryLog.objects.filter(xlmm=xlmm, carry_date__gte=left_date, carry_date__lte=right_date)
        referals = referal_From(xlmm_obj.mobile)  # 推荐代理状况
        refs_num = referals.count()
        data = {"xlmm_obj": xlmm_obj, "clickcounts": clickcounts, "carry_log_all_sum": carry_log_all_sum,
                "order_counts": order_counts, "referals": referals, "allcarrylogs": allcarrylogs,
                "xlmm": xlmm, "left_date": left_date,
                "right": right_date, "sum_detail_pending": sum_detail_pending,
                "sum_detail_confirm": sum_detail_confirm, 'total_clicks': total_clicks,
                'total_orders': total_orders, 'refs_num': refs_num}
        return data

    def get(self, request):
        data = self.calcu_data(request)
        return render_to_response(self.template, data, context_instance=RequestContext(request))

    def post(self, request):
        data = self.calcu_data(request)
        return render_to_response(self.template, data, context_instance=RequestContext(request))


class XlmmExit(object):
    """ 代理退出 """

    def __init__(self, xlmm):
        self.xlmm = xlmm

    def check_xlmm_available(self, xlmm):
        if xlmm.charge_status != XiaoluMama.CHARGED:
            return
        if xlmm.agencylevel < XiaoluMama.VIP_LEVEL:
            return None
        else:
            return xlmm

    def check_carry_in(self, xlmm_id):
        """ 代理总收入 """
        clgs = CarryLog.objects.filter(xlmm=xlmm_id, carry_type=CarryLog.CARRY_IN, status=CarryLog.CONFIRMED)
        value_in = clgs.aggregate(total_value=Sum('value')).get('total_value') or 0
        return value_in

    def check_carry_out(self, xlmm_id):
        """ 代理总支出 """
        clgs = CarryLog.objects.filter(xlmm=xlmm_id, carry_type=CarryLog.CARRY_OUT, status=CarryLog.CONFIRMED)
        value_out = clgs.aggregate(total_value=Sum('value')).get('total_value') or 0
        return value_out

    def calculate_cost_flush(self, carry_ins, carry_outs):
        """ 计算补差数额 """
        # 加入就退出并且可以有30的奖励
        flush_value = carry_ins - carry_outs
        return flush_value

    def create_flush_log(self, xlmm_id, flush_value):
        """ 创建补差额记录 """
        # 补差额生成 判断类型
        if flush_value > 0:  # 收入大于支出 补差为支出
            CarryLog.objects.create(xlmm=xlmm_id, log_type=CarryLog.COST_FLUSH, status=CarryLog.CONFIRMED,
                                    carry_type=CarryLog.CARRY_OUT, value=flush_value)
        elif flush_value < 0:  # 收入小于支出 补差为收入
            CarryLog.objects.create(xlmm=xlmm_id, log_type=CarryLog.COST_FLUSH, status=CarryLog.CONFIRMED,
                                    carry_type=CarryLog.CARRY_IN, value=flush_value)
        else:  # 等于0 的情况则不去创建
            pass

    def modify_xlmm_base_info(self, xlmm):
        """ 修改代理到初始状态 """
        xlmm.cash = 0
        xlmm.agencylevel = XiaoluMama.INNER_LEVEL
        xlmm.charge_status = XiaoluMama.UNCHARGE
        xlmm.target_complete = 0
        xlmm.hasale = False
        xlmm.user_group_id = None
        xlmm.referal_from = ''
        xlmm.pending = 0
        xlmm.manager = 0
        xlmm.charge_time = None
        xlmm.renew_time = None
        xlmm.last_renew_type = XiaoluMama.FULL
        update_model_fields(xlmm,
                            update_fields=['cash', 'agencylevel', 'charge_status', 'target_complete', 'hasale',
                                           'user_group', 'referal_from', 'pending', 'manager', 'charge_time',
                                           'renew_time', 'last_renew_type'])
        return xlmm

    def xlmm_buy_cash(self, xlmm):
        clgs_buy = CarryLog.objects.filter(xlmm=xlmm.id, carry_type=CarryLog.CARRY_OUT, log_type=CarryLog.ORDER_BUY,
                                           status=CarryLog.CONFIRMED)
        clgs_refund = CarryLog.objects.filter(xlmm=xlmm.id, carry_type=CarryLog.CARRY_IN,
                                              log_type=CarryLog.REFUND_RETURN, status=CarryLog.CONFIRMED)
        value_buy = clgs_buy.aggregate(total_value=Sum('value')).get('total_value') or 0
        value_refund = clgs_refund.aggregate(total_value=Sum('value')).get('total_value') or 0
        return value_buy - value_refund

    def modify_lowest_uncoushout(self, xlmm):
        """ 将消费记录填写到最低不可提现金额里面　"""
        value_buy = self.xlmm_buy_cash(xlmm)  # 消费
        # 之前的充值是不能提现　的　所以都会产生在消费记录当中　　所以这里要将消费记录的数值写入最低不可提现字段
        xlmm.lowest_uncoushout = value_buy / 100.0
        update_model_fields(xlmm, update_fields=['lowest_uncoushout'])

    def xlmmexit(self):
        """ 代理退出操作 """
        xlmm = self.check_xlmm_available(self.xlmm)  # 检查账户是否有效
        if xlmm is None:
            return "mm_error_status"
        carry_ins = self.check_carry_in(self.xlmm.id)  # 计算收入
        carry_outs = self.check_carry_out(self.xlmm.id)  # 计算支出
        flush_value = self.calculate_cost_flush(carry_ins, carry_outs)  # 计算补差额
        self.create_flush_log(self.xlmm.id, flush_value)  # 生成补差记录
        self.modify_xlmm_base_info(self.xlmm)  # 修改该代理账户 基本信息
        self.modify_lowest_uncoushout(xlmm)
        return flush_value / 100.0


def xlmmExitAction(request):
    """ 执行代理退出 """
    content = request.GET
    xlmm_id = content.get("xlmm_id", None)
    if xlmm_id is None:
        return HttpResponse({"error": "编号为空"})
    xlmm = get_object_or_404(XiaoluMama, id=xlmm_id)
    exit_xlmm = XlmmExit(xlmm)
    flush_cash = exit_xlmm.xlmmexit()
    log_action(request.user.id, xlmm, CHANGE, u'代理退出修改信息')
    data = {"flush_cash": flush_cash}
    return HttpResponse(json.dumps(data))
