__author__ = 'yann'
# -*- coding:utf-8 -*-
import datetime
from django.views.generic import View
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.template import RequestContext
from flashsale.xiaolumm.models import XiaoluMama
from .models import StatisticsShopping, StatisticsShoppingByDay
from django.http import HttpResponse


class StatisticTongJi(View):
    def getUserName(self, uid):
        try:
            return User.objects.get(pk=uid).username
        except:
            return 'none'

    def get(self, request):
        content = request.GET
        daystr = content.get("day", None)
        pk = content.get('pk', '1')

        today = datetime.date.today()
        target_date = today
        if daystr:
            year, month, day = daystr.split('-')
            target_date = datetime.date(int(year), int(month), int(day))
            if target_date > today:
                target_date = today
        time_from = datetime.datetime(target_date.year, target_date.month, target_date.day)
        time_to = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)
        if target_date == today:
            time_to = datetime.datetime.now()

        prev_day = target_date - datetime.timedelta(days=1)
        next_day = None
        if target_date < today:
            next_day = target_date + datetime.timedelta(days=1)

        XLmamas = XiaoluMama.objects.all()
        data = StatisticsShopping.objects.filter(shoptime__range=(time_from, time_to)).filter(linkid=pk)
        countdata = StatisticsShoppingByDay.objects.filter(linkid=pk, tongjidate=target_date)
        if countdata:
            countdata = countdata[0]
        return render_to_response("shopstats.html",
                                  {'pk': int(pk), "data": data, "xiaolumamas": XLmamas, "countdata": countdata,
                                   "prev_day": prev_day,
                                   "target_date": target_date, "next_day": next_day},
                                  context_instance=RequestContext(request))


from flashsale.clickrebeta import tasks


def ShengChengAll(req):
    tasks.task_Tongji_All_Order.delay()
    return HttpResponse("OK")
