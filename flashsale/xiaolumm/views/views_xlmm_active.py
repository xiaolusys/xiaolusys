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
    default_active_num = 5

    def date_zone(self, request):
        """ 获取日期区间　"""
        content = request.GET
        date_from = content.get('date_from', None)
        date_to = content.get('date_to', None)
        if date_from is None or date_to is None:
            date_from = datetime.date.today() - datetime.timedelta(days=15)
            date_to = datetime.date.today()
            return date_from, date_to
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
        xlmm_clicks = queryset.values('date').annotate(s_valid_num=Sum('valid_num'))
        return xlmm_clicks

    def user_query(self, queryset):
        user_nums = queryset.values('date').annotate(s_user_num=Sum('user_num'))
        return user_nums

    def get(self, request):
        if request.user.has_perm('xiaolumm.browser_xlmm_active'):
            date_from, today = self.date_zone(request)
            ac_queryset, queryset = self.filter_queryset(date_from, today)
            ac_record = ac_queryset.count()
            total_record = queryset.count()
            tol_da = self.click_query(queryset)
            user_da = self.user_query(queryset)
            return Response(
                {"date_from": date_from, "today": today, 'ac_day': [ac_record, total_record], 'tol_da': tol_da,
                 'user_da': user_da})
        else:
            return Response({})

    def post(self, request):
        if request.user.has_perm('xiaolumm.browser_xlmm_active'):
            date_from, today = self.date_zone(request)
            ac_queryset, queryset = self.filter_queryset(date_from, today)
            ac_record = ac_queryset.count()
            total_record = queryset.count()
            tol_da = self.click_query(queryset)
            user_da = self.user_query(queryset)
            return Response({'ac_day': [ac_record, total_record], 'tol_da': tol_da, 'user_da': user_da})
        else:
            return Response({})
