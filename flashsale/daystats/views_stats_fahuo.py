# coding:utf-8
from rest_framework import generics
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response
import datetime
from calendar import monthrange
from flashsale.dinghuo.models import DailyStatsPreview
from django.forms.models import model_to_dict


class StatsFahuoView(generics.ListCreateAPIView):
    """
        日汇总表
    """
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "xiaolumm/huizong/hui_zong_chart.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=monthrange(today.year, today.month)[1])
        end_date = today
        return Response({"start_date": start_date, "end_date": end_date})

    def post(self, request, *args, **kwargs):
        content = request.REQUEST
        today = datetime.date.today()
        start_time_str = content.get("date_from", None)
        end_time_str = content.get("date_to", None)
        if start_time_str:
            year, month, day = start_time_str.split('-')
            start_date = datetime.date(int(year), int(month), int(day))
            if start_date > today:
                start_date = today
        else:
            start_date = today - datetime.timedelta(days=monthrange(today.year, today.month)[1])
        if end_time_str:
            year, month, day = end_time_str.split('-')
            end_date = datetime.date(int(year), int(month), int(day))
        else:
            end_date = today

        all_data = DailyStatsPreview.objects.filter(sale_time__range=(start_date, end_date)).order_by("sale_time")
        result_data = []
        for one_data in all_data:
            rate_dic = {'sale_time': one_data.sale_time, 'time_to_day': one_data.time_to_day}
            result_data.append(rate_dic)
        # result_data = [ {'sale_time': "2015-9-10", 'time_to_day': 1.2},
        #                 {'sale_time': "2015-9-13", 'time_to_day': 2.4},
        #                 {'sale_time': "2015-9-14", 'time_to_day': 4.3},
        #                 {'sale_time': "2015-9-15", 'time_to_day': 4.2},
        #                 {'sale_time': "2015-9-17", 'time_to_day': 9.4},
        #                 {'sale_time': "2015-10-10", 'time_to_day': 0.5}]
        return Response(result_data)
