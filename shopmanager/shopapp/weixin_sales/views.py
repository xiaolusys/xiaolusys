#-*- encoding:utf8 -*-
import json
import datetime
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from shopback.base.authentication import login_required_ajax
from .models import WeixinUserPicture

@csrf_exempt
@login_required_ajax
def picture_review(request):
    
    content = request.REQUEST
    
    rows    =  WeixinUserPicture.objects.filter(id = content.get('pid'))\
                .update(status=WeixinUserPicture.COMPLETE)
    
    return  HttpResponse(json.dumps({'code':(1,0)[rows]}),mimetype="application/json")