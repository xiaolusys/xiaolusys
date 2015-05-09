# coding=utf-8
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from clickcount.models import ClickCount
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


def write_all_user_click(request):
    # 将昨天所有小鹿妈妈们的点击统计写统计数据到表中
    today = datetime.date.today()  # 今天的日期
    oneday = datetime.timedelta(days=1)
    yesterday = today - oneday  # 昨天

    time_from = datetime.datetime(yesterday.year, yesterday.month, yesterday.day)  # 生成带时间的格式  开始时间
    time_to = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)  # 停止时间

    xiaolumamas = XiaoluMama.objects.all()  # 所有小鹿妈妈们
    for xiaolumama in xiaolumamas:  #
        clicks = Clicks.objects.filter(linkid=xiaolumama.id).filter(created__gt=time_from,
                                                                    created__lt=time_to)  # 根据代理的id过滤出点击表中属于该代理的点击
        if clicks:  # 如果昨天有对应的小鹿妈妈的点击存在
            clickcount = ClickCount()  # 新建一个统计实例 待写入    # 一定要在写入之前 创建  在 如果在FOR循环外面 则会出现后来数据重写到同一个 中
            clickcount.number = xiaolumama.id  # 写ID到统计表
            clickcount.name = xiaolumama.weikefu  # 写名字到统计表
            frequency = clicks.count()  # 点击数量
            nop = clicks.values('openid').distinct().count()  # 点击人数
            clickcount.administrator = xiaolumama.manager  # 接管人
            clickcount.frequency = frequency
            clickcount.nop = nop
            clickcount.date = yesterday
            clickcount.save()
        else:
            HttpResponse('clicks object has not found !')
    return HttpResponse("click count is ok !")


def show_all(request):
    clickcounts = ClickCount.objects.all()
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



