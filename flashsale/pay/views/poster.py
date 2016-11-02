# coding=utf-8
"""
从排期管理中上传海报
"""
import json
import datetime
from django.views.generic import View
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from common.modelutils import update_model_fields
from core.options import log_action, ADDITION, CHANGE
from flashsale.pay.models import GoodShelf

class PostGoodShelf(View):
    template = "poster/upload_poster.html"

    def get(self, request):
        content = request.REQUEST
        date = content.get('date', None)
        categray = content.get('categray', None)
        if categray == "child":
            categray = "童装"
        elif categray == "female":
            categray = "女装"
        return render_to_response('poster/upload_poster.html', {"date": date, "categray": categray},
                                  context_instance=RequestContext(request))

    def post(self, request):
        content = request.REQUEST
        date = content.get("date", None)
        categray = content.get("categray", None)
        pic_link = content.get("pic_link", None)
        if pic_link is None or date is None or categray is None:
            data = {"code": 0}  # 确少参数
            return HttpResponse(json.dumps(data))  # 传图为空
        date_desc = date + '_poster'
        year, month, day = map(int, date.split('-'))
        active_time = datetime.datetime(year, month, day, 9, 30, 0)
        active_time_from = datetime.datetime(year, month, day, 0, 0, 0)
        active_time_to = datetime.datetime(year, month, day, 23, 59, 59)
        try:
            goodshelf, state = GoodShelf.objects.get_or_create(active_time__gte=active_time_from,
                                                               active_time__lte=active_time_to)
            if categray == "child":
                GoodShelf.DEFAULT_CHD_POSTER[0]['pic_link'] = pic_link
                chd_posters = GoodShelf.DEFAULT_CHD_POSTER
                goodshelf.chd_posters = chd_posters
                update_model_fields(goodshelf, update_fields=['chd_posters'])
                data = {"code": 1}  # 修改童装海报成功
                log_action(request.user.id, goodshelf, CHANGE, u'修改童装海报成功')
            elif categray == "female":
                GoodShelf.DEFAULT_WEN_POSTER[0]['pic_link'] = pic_link
                goodshelf.wem_posters = GoodShelf.DEFAULT_WEN_POSTER
                update_model_fields(goodshelf, update_fields=['wem_posters'])
                log_action(request.user.id, goodshelf, CHANGE, u'修改女装海报成功')
                data = {"code": 2}  # 修改女装海报成功
            else:
                data = {"code": 5}  # 类别缺失
            # 上线日期
            goodshelf.title = date_desc
            goodshelf.active_time = active_time
            update_model_fields(goodshelf, update_fields=['title', 'active_time'])
            log_action(request.user.id, goodshelf, CHANGE, u'修改海报上线日期')

            # 创建次日海报
            next_day_from = active_time_from + datetime.timedelta(days=1)
            next_day_to = active_time_to + datetime.timedelta(days=1)
            next_day_gs, state_next = GoodShelf.objects.get_or_create(active_time__gte=next_day_from,
                                                                      active_time__lte=next_day_to)
            next_day_gs.title = goodshelf.title + '_next'
            next_day_gs.chd_posters = goodshelf.chd_posters
            next_day_gs.wem_posters = goodshelf.wem_posters
            next_day_gs.active_time = active_time + datetime.timedelta(days=1)
            update_model_fields(next_day_gs, update_fields=['title', 'active_time', 'chd_posters', 'wem_posters'])
            if state_next:
                log_action(request.user.id, next_day_gs, ADDITION, u'新建海报成功')
            else:
                log_action(request.user.id, next_day_gs, CHANGE, u'修改海报成功')

            return HttpResponse(json.dumps(data))  # 传图成功
        except GoodShelf.MultipleObjectsReturned:
            data = {'code': 3}  # 多个海报对象
            return HttpResponse(json.dumps(data))
        except ValueError:
            data = {'code': 4}  # ValueError
            return HttpResponse(json.dumps(data))
