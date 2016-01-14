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
        content = request.REQUEST
        today = datetime.date.today()
        target_day = content.get("target_day", today.strftime("%Y-%m-%d"))
        target_day = datetime.datetime.strptime(target_day, '%Y-%m-%d')
        auther = request.user.get_full_name()
        target_day_tomorow = target_day + datetime.timedelta(days=1)
        today_query = self.queryset.filter(start_time__gte=target_day, start_time__lt=target_day_tomorow).order_by(
            'start_time')
        return Response({"auther": auther, "date": target_day.date(), "today_query": today_query,
                         "target_day_tomorow": target_day_tomorow.date(),
                         "category_choices": NinePicAdver.CATEGORY_CHOICE})

    def post(self, request):
        content = request.REQUEST
        start_time = content.get('start_time', None)
        title = content.get("title", None)
        turns_num = content.get('turns_num', None)
        pic_arry = content.get('pic_arry', None)
        pic_arry = pic_arry.split(',')
        auther = request.user.get_full_name()
        cate_gory = content.get("cate_gory", 9)
        try:
            start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d%H:%M:%S')
        except ValueError:
            now = datetime.datetime.now()
            start_time = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, 0)
        ninepic = NinePicAdver.objects.create(title=title, start_time=start_time, pic_arry=pic_arry,
                                              turns_num=turns_num, cate_gory=cate_gory,
                                              auther=auther)
        log_action(request.user.id, ninepic, ADDITION, "添加九张图")
        return Response({"code": 1})
