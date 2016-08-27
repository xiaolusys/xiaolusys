# encoding=utf8
from datetime import datetime, timedelta
from django.shortcuts import render
from django.db.models import Sum

from flashsale.pay.models.user import Customer
from flashsale.xiaolumm.models.models import XiaoluMama
from flashsale.pay.models.trade import SaleTrade


def index(req):
    now = datetime.now()
    today = datetime(now.year, now.month, now.day)
    yesterday = today - timedelta(days=1)

    customer_today_count = Customer.objects.using('product').filter(created__gte=today).count()
    customer_yesterday_count = Customer.objects.using('product')\
                                               .filter(created__gte=yesterday, created__lt=today).count()

    xlmm_today_count = XiaoluMama.objects.using('product').filter(created__gte=today).count()
    xlmm_yesterday_count = XiaoluMama.objects.using('product').filter(created__gte=yesterday, created__lt=today).count()

    trade_today_count = SaleTrade.objects.using('product').filter(created__gte=today).count()
    trade_pay_today_count = SaleTrade.objects.using('product').filter(pay_time__gte=today).count()
    trade_pay_today_fee = SaleTrade.objects.using('product')\
                                           .filter(pay_time__gte=today).aggregate(Sum('total_fee'))['total_fee__sum']

    trade_yesterday_count = SaleTrade.objects.using('product').filter(created__gte=yesterday, created__lt=today).count()
    trade_pay_yesterday_count = SaleTrade.objects.using('product') \
                                                 .filter(pay_time__gte=yesterday, pay_time__lt=today).count()
    trade_pay_yesterday_fee = SaleTrade.objects.using('product') \
                                       .filter(pay_time__gte=yesterday, pay_time__lt=today) \
                                       .aggregate(Sum('total_fee'))['total_fee__sum']

    return render(req, 'yunying/index.html', locals())
