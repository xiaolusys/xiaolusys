import json
from django.http import HttpResponse
from auth import staff_requried
from auth.utils import parse_datetime,parse_date,format_time,map_int2str
from shopback.logistics.tasks import updateAllUserOrdersLogisticsTask

__author__ = 'meixqhi'


@staff_requried(login_url='/admin/login/')
def update_interval_logistics(request,dt_f,dt_t):

    dt_f = parse_date(dt_f)
    dt_t = parse_date(dt_t)

    logistics_task = updateAllUserOrdersLogisticsTask.delay(update_from=dt_f,update_to=dt_t)

    ret_params = {'task_id':logistics_task.task_id}

    return HttpResponse(json.dumps(ret_params),mimetype='application/json')