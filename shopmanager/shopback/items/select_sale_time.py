# coding=utf-8
#__author__ = 'linjie'
from .models import Product
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.template import RequestContext
from django.http import HttpResponse
import datetime
from flashsale.dinghuo import log_action, CHANGE

@csrf_exempt
@transaction.commit_on_success
def change_Sale_Time(request):
    # sale_time 上架日期
    content = request.POST
    item_id = content.get('item_id')
    sale_time = content.get('sale_time')
    if sale_time:
        year, month, day = sale_time.split('-')
        date = datetime.date(int(year), int(month), int(day))
    else:
        return HttpResponse('false')
    pro = Product.objects.filter(id=item_id)
    if pro.exists():
        p = pro[0]
        p.sale_time = date
        p.save()
        log_action(request.user.id, p, CHANGE, u'修改商品的上架日期')
        return HttpResponse('OK')

    else:
        return HttpResponse('false')



