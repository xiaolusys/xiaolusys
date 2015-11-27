# coding=utf-8
"""　xlmm　活跃度统计
所有代理　活跃天数占比
"""
from flashsale.clickcount.models import ClickCount
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
import datetime
from django.db.models import Sum


class XlmmActive(APIView):
    queryset = ClickCount.objects.all()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "analysis/xlmm_active.html"
    date_from = datetime.date.today() - datetime.timedelta(days=15)
    date_to = datetime.date.today()
    default_active_num = 5

    def date_zone(self, request):
        """ 获取日期区间　"""
        content = request.REQUEST
        date_from = content.get('date_from', None)
        date_to = content.get('date_to', None)
        if date_from is None or date_to is None:
            return self.date_from, self.date_to
        year, month, day = map(int, date_from.split('-'))
        date_from = datetime.date(year, month, day)
        year, month, day = map(int, date_to.split('-'))
        date_to = datetime.date(year, month, day)
        return date_from, date_to

    def filter_queryset(self, date_from, tate_to):
        """ 过滤时间段的对象集　"""
        queryset = self.queryset.filter(date__gte=date_from, date__lte=tate_to)  # 总集合
        active_queryset = queryset.filter(valid_num__gte=self.default_active_num)  # 活跃集合
        return active_queryset, queryset

    def click_query(self, queryset):
        xlmm_clicks = queryset.values('linkid', 'date').annotate(s_valid_num=Sum('valid_num'))
        return xlmm_clicks

    def calcu_ac_dic(self, ac_da):
        active_dic = {}
        for rcdd in ac_da:
            rcd = rcdd['linkid']
            if active_dic.has_key(rcd):
                active_dic[rcd] += 1
            else:
                active_dic[rcd] = 1
        return active_dic

    def get(self, request):
        if request.user.has_perm('clickcount.browser_xlmm_active'):
            date_from, today = self.date_zone(request)
            ac_queryset, queryset = self.filter_queryset(date_from, today)
            ac_da = self.click_query(ac_queryset)
            tol_da = self.click_query(queryset)
            active_dic = self.calcu_ac_dic(ac_da)
            return Response(
                {"date_from": date_from, "today": today, 'ac_da': ac_da, 'tol_da': tol_da, 'active_dic': active_dic})
        else:
            return Response({})

    def post(self, request):
        if request.user.has_perm('clickcount.browser_xlmm_active'):
            date_from, today = self.date_zone(request)
            ac_queryset, queryset = self.filter_queryset(date_from, today)
            ac_da = self.click_query(ac_queryset)
            tol_da = self.click_query(queryset)
            active_dic = self.calcu_ac_dic(ac_da)
            return Response({'ac_da': ac_da, 'tol_da': tol_da, 'active_dic': active_dic})
        else:
            return Response({})


