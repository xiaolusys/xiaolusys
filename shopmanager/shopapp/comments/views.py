#-*- encoding:utf8 -*-
import json
import datetime
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from shopback.base.authentication import login_required_ajax
from shopapp.comments.models import Comment
import logging


logger = logging.getLogger('django.request')

@login_required_ajax
def comment_not_need_explain(request,id):
    
    rows =  Comment.objects.filter(id = id).update(ignored = True)
    
    return  HttpResponse(json.dumps({'code':(1,0)[rows]}),mimetype="application/json")


@csrf_exempt
@login_required_ajax
def explain_for_comment(request):
    
    content = request.REQUEST
    cid     = content.get('cid')
    reply   = content.get('reply')
    
    try:
        comment = Comment.objects.get(id=cid)
    
        comment.reply_order_comment(reply)
    except Exception,exc:
        logger.error(exc.message or str(exc),exc_info=True)
        return HttpResponse(json.dumps({'code':1,'error_response':exc.message}),mimetype="application/json")
    
    return  HttpResponse(json.dumps({'code':0,'response_content':'success'}),mimetype="application/json")
