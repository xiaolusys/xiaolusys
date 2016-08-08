# coding=utf-8
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from flashsale.xiaolumm.models import CashOut, XiaoluMama, CarryLog
import datetime
from core.options import log_action, CHANGE
from django.db.models import Sum


class CashoutBatView(APIView):
    """ 批量处理提现功能 """
    queryset = CashOut.objects.all()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "cashout/cashout_bathandler.html"
    show_lit_num = 50

    def get_data(selef, cashouts):
        """ 计算返回页面要求数数据 """
        data = []
        for cashout in cashouts:
            xlmm_id = cashout.xlmm
            value = cashout.get_value_display()
            mm = XiaoluMama.objects.get(pk=xlmm_id)
            could_cash_out = mm.get_cash_iters()
            mm_carrys = CarryLog.objects.filter(xlmm=xlmm_id, status=CarryLog.CONFIRMED)  # 代理收支记录
            carrylogs_in = mm_carrys.filter(carry_type=CarryLog.CARRY_IN)  # 收入
            carrylogs_out = mm_carrys.filter(carry_type=CarryLog.CARRY_OUT)  # 支出
            svin = carrylogs_in.aggregate(total_carry_in=Sum('value')).get('total_carry_in') or 0
            svout = carrylogs_out.aggregate(total_carry_out=Sum('value')).get('total_carry_out') or 0
            sum_carry_in = svin / 100.0
            sum_carry_out = svout / 100.0
            minus = sum_carry_in - sum_carry_out
            data_entry = {'id': cashout.id, 'xlmm': xlmm_id, 'value': value, 'mobile': mm.mobile,
                          'cash': mm.get_cash_display(),
                          'could_cash_out': could_cash_out, 'sum_carry_in': sum_carry_in,
                          'sum_carry_out': sum_carry_out, 'minus': minus}
            data.append(data_entry)
        return data

    def get(self, request):
        content = request.REQUEST
        today = datetime.date.today()
        target_day = content.get("target_day", today.strftime("%Y-%m-%d"))  # 目标日期
        target_day = datetime.datetime.strptime(target_day, '%Y-%m-%d')
        user = request.user.get_full_name()
        target_day_tomorow = target_day + datetime.timedelta(days=1)
        target_day_yestoday = target_day - datetime.timedelta(days=1)
        today_query = self.queryset.filter(created__gte=target_day, status=CashOut.PENDING,
                                           created__lt=target_day_tomorow).order_by('created')
        data = self.get_data(today_query[0:self.show_lit_num])
        return Response({"user": user, "date": target_day.date(), "data": data,
                         "target_day_tomorow": target_day_tomorow.date(),
                         "target_day_yestoday": target_day_yestoday.date()})

    def post(self, request):
        if not request.user.has_perm('xiaolumm.xiaolumm_cashout_bat_handler'):
            return Response({"code": 2})  # 没有权限
        content = request.REQUEST
        cashout_ids = content.get('cashout_ids', None)
        if cashout_ids is None:
            return Response({"code": 1})  # 没有参数
        cashoutids = cashout_ids.split('-')
        allow_cashouts = CashOut.objects.filter(id__in=cashoutids, status=CashOut.PENDING)
        for allow in allow_cashouts:
            arg = allow.approve_cashout()
            if arg: log_action(request.user.id, allow, CHANGE, u"提现批量审核通过")  # 如果返回真则记录操作日志
        return Response({"code": 0})
