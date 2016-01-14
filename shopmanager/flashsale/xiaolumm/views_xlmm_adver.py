# coding=utf-8
"""　
九张图
"""
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from .models_advertis import NinePicAdver
import datetime
from shopback.base import log_action, ADDITION


class NinepicView(APIView):
    """ 九张图 """
    queryset = NinePicAdver.objects.all()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "advertise/nine_pic.html"
    default_active_num = 5

    def get(self, request):
        today = datetime.date.today()
        auther = request.user.get_full_name()
        monday = today + datetime.timedelta(days=1)
        today_query = self.queryset.filter(start_time__gte=today, start_time__lt=monday)
        return Response({"auther": auther, "date": today, "today_query": today_query})

    def post(self, request):
        content = request.REQUEST
        start_time = content.get('start_time', None)
        title = content.get("title", None)
        turns_num = content.get('turns_num', None)
        pic_arry = content.get('pic_arry', None)
        pic_arry = pic_arry.split(',')
        auther = request.user.get_full_name()
        start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        ninepic = NinePicAdver.objects.create(title=title, start_time=start_time, pic_arry=pic_arry,
                                              turns_num=turns_num,
                                              auther=auther)
        log_action(request.user.id, ninepic, ADDITION, "添加九张图")
        return Response({"code": 1})
