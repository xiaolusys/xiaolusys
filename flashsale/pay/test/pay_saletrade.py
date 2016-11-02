from flashsale.pay.models import SaleTrade
from django.db.models import Sum
import datetime

def check_sale_trade_total():
    SaleTrade.objects.filter(status__in=[2,3,4,5], pay_time__gte=datetime.datetime(2016,9,30),pay_time__lte=datetime.datetime(2016,10,31)).aggregate(Sum('total_fee'))