# encoding=utf8
import simplejson
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from flashsale.daystats.mylib.wangdiantong import WangDianTong


@login_required
def index(req):
    page = req.GET.get('page') or 1
    wdt = WangDianTong()
    result = wdt.get_products(page_no=page)
    items = result['GoodsList']['Goods']

    count = int(result['TotalCount'])
    cur_page = {
        'has_previous': '',
        'has_next': '',
        'number': int(page),
    }
    p = {}
    p['show_page_range'] = [x+1 for x in range(count/40+1)]
    return render(req, 'yunying/wdt/index.html', locals())
