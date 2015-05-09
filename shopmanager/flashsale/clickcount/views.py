# coding=utf-8
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from .models import ClickCount
from shopmanager.flashsale.xiaolumm.models import Clicks, XiaoluMama
import datetime
import json
from django.forms import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import User


def clickcount(request):
    today = datetime.date.today()  # 今天的日期
    oneday = datetime.timedelta(days=1)
    yesterday = today - oneday  # 昨天
    user = request.user
    filterid = user.id
    clickcounts = ClickCount.objects.filter(administrator=filterid).filter(date=yesterday)
    users = User.objects.all()
    return render(request, "click_count.html", {"clickcounts": clickcounts, "users": users})


def bydate(request):
    # 根据页面传来的日期 挑选出当前用户的该日期的点击统计
    response = HttpResponse()
    response['Content-Type'] = "text/javascript"
    date = request.GET.get("date", "")
    # 处理date
    today = datetime.date.today()  # 今天的日期
    month, day, year = date.split('/')
    target_date = datetime.date(int(year), int(month), int(day))
    if target_date > today:
        target_date = today

    clickcounts = ClickCount.objects.filter(date=target_date, administrator=request.user.id)
    # 返回json
    clickcount_list = []
    for clickcount in clickcounts:
        # username User
        user = User.objects.get(id=clickcount.administrator)
        clickcount_dict = model_to_dict(clickcount)
        clickcount_dict['write_time'] = clickcount.write_time
        clickcount_dict['administrator'] = user.username
        clickcount_list.append(clickcount_dict)
    return HttpResponse(json.dumps(clickcount_list, cls=DjangoJSONEncoder))



