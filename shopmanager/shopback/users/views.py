#-*- coding:utf8 -*-
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User as DjangoUser
from shopback.base.authentication import login_required_ajax

@csrf_exempt
@login_required_ajax
def get_usernames_by_segstr(request):
    
    content = request.REQUEST
    q       = content.get('term')
    if not q:
        ret = {'code':1,'error_response':u'查询内容不能为空'}
        return HttpResponse(json.dumps(ret),mimetype="application/json")
    
    valuelist = DjangoUser.objects.filter(username__startswith=q).values_list('username')
    usernames = [{'id':'everyone','label':'everyone','value':'everyone'}]
    if valuelist:
        for vl in valuelist[0]:
            usernames.append({'id':vl,'label':vl,'value':vl})
    return HttpResponse(json.dumps(usernames),mimetype="application/json")
    
    