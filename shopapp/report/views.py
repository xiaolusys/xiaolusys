# -*- coding: utf-8 -*-
import json
import datetime
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from auth import staff_requried
from common.utils import parse_datetime, parse_date, format_time, map_int2str
from shopapp.report.tasks import updateMonthTradeXlsFileTask


@staff_requried(login_url=settings.LOGIN_URL)
def gen_report_form_file(request):
    content = request.REQUEST
    year = content.get('year', None)
    month = content.get('month', None)
    update_month_trade_task = updateMonthTradeXlsFileTask.delay(year=year, month=month)

    ret_params = {'task_id': update_month_trade_task.task_id}

    return HttpResponse(json.dumps(ret_params), content_type='application/json')
