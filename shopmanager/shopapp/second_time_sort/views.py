#-*- coding:utf-8 -*-
import time
import json
import random
import datetime
from django.http import HttpResponse 
from django.template import RequestContext
from django.shortcuts import render_to_response
from .models import BatchNumberGroup,BatchNumberOid
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def batch_number(request):
    content = request.GET
    group   = content.get('group')
    group = int(group)

    created = datetime.datetime.now()
    batch_object = BatchNumberGroup.objects.create(group=group,created=created)
    
    return  HttpResponse(json.dumps({'bid':batch_object.pk}),mimetype="application/json")
 
def batch_pick(request):
    return render_to_response('second_time_sort/sort_admin.html', 
                              {'group':1},context_instance=RequestContext(request))
                              
                              
def write_batch_outSid(batchNumber,out_sid,group):
    batch_o,state = BatchNumberOid.objects.get_or_create(batch_number=batchNumber,out_sid=out_sid,group=group)
    batch_o.save()

    
def batch_number_out(request):
    content = request.POST
    out_sid = content.get('outSid')
    group   = content.get('group')
    print "group%333333333333333333333333333333333333%%%%%",group
    print "out_sid&&&333333333333333333333333333333333333333&&&&&",out_sid
    return ''
    