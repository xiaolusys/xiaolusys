# -*- coding:utf8 -*-
import datetime
import json
from django.http import HttpResponse
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from common.utils import parse_datetime, parse_date, format_time, map_int2str
from shopback.amounts.tasks import updateAllUserOrdersAmountTask


@staff_member_required
def update_finish_trade_amount(request, dt_f, dt_t):
    dt_f = parse_date(dt_f)
    dt_t = parse_date(dt_t)

    order_amount_task = updateAllUserOrdersAmountTask.delay(dt_f=dt_f, dt_t=dt_t)

    ret_params = {'task_id': order_amount_task.task_id}

    return HttpResponse(json.dumps(ret_params), content_type='application/json')
