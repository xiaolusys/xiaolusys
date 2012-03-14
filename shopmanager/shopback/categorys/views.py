import json
from django.http import HttpResponse
from shopback.categorys.tasks import RecurUpdateCategoreyTask

def crawFullCategories(request,cid):

    top_session = request.session['top_session']

    RecurUpdateCategoreyTask.delay(top_session,cid)

    return HttpResponse(json.dumps({'code':0}))



  