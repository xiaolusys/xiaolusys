# coding=utf-8
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework import permissions
from tasks import xlmmClickTop, xlmmOrderTop
import datetime


def timeZone(time_from=None, time_to=None):
    if time_from and time_to:
        year_f, month_f, day_f = time_from.split("-")
        year_t, month_t, day_t = time_to.split("-")
        time_from = datetime.datetime(int(year_f), int(month_f), int(day_f), 0, 0, 0)
        time_to = datetime.datetime(int(year_t), int(month_t), int(day_t), 0, 0, 0)
        return time_from, time_to
    else:
        return datetime.datetime.now() - datetime.timedelta(days=7), datetime.datetime.now()


class TopDataView(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "top_50/top_api_page.html"

    permission_classes = (permissions.IsAuthenticated,)

    def getClickTopTaskid(self, time_from, time_to):
        taskid = xlmmClickTop.delay(time_from, time_to)
        return taskid

    def getOrderTopTaskid(self, time_from, time_to):
        taskid = xlmmOrderTop.delay(time_from, time_to)
        return taskid

    def get(self, request, format=None):
        content = request.GET
        t_from = (content.get('time_from', None))
        t_to = (content.get('time_to', None))
        func = (content.get('func', None))
        time_from, time_to = timeZone(t_from, t_to)

        if func == "click_top" and time_to and time_from:
            # 调用点击top50的函数
            taskobj = self.getClickTopTaskid(time_from, time_to)
            return Response({"task_id": taskobj.task_id})

        if func == "order_top" and time_to and time_from:
            # 调用点击top50的函数
            taskobj = self.getOrderTopTaskid(time_from, time_to)
            return Response({"task_id": taskobj.task_id})
        else:
            return Response({"task_id": "none"})
