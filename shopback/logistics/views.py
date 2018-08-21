import json
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from common.utils import parse_datetime, parse_date, format_time, map_int2str
from shopback.logistics.tasks import updateAllUserOrdersLogisticsTask
from shopback.logistics.models import Logistics, LogisticsCompany
from shopapp.taobao import apis

__author__ = 'meixqhi'


@login_required(login_url=settings.LOGIN_URL)
def update_logistics_company(request):
    profile = request.user.get_profile()
    response = apis.taobao_logistics_companies_get(tb_user_id=profile.visitor_id)
    logistics_company = response['logistics_companies_get_response']['logistics_companies']['logistics_company']
    for company in logistics_company:
        LogisticsCompany.save_logistics_company_through_dict(profile.visitor_id, company)

    return HttpResponse(json.dumps({'code': 0, 'response': 'ok'}), content_type='application/json')


@staff_member_required
def update_interval_logistics(request, dt_f, dt_t):
    dt_f = parse_date(dt_f)
    dt_t = parse_date(dt_t)

    logistics_task = updateAllUserOrdersLogisticsTask.delay(update_from=dt_f, update_to=dt_t)

    ret_params = {'task_id': logistics_task.task_id}

    return HttpResponse(json.dumps(ret_params), content_type='application/json')
