# -*- coding:utf-8 -*-
import time
import json
import random
import datetime
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from .models import BatchNumberGroup, BatchNumberOid
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def batch_pick(request):
    return render_to_response('second_time_sort/sort_admin.html',
                              {'group': 1, "batch_number": '-1',}, context_instance=RequestContext(request))


@csrf_exempt
def batch_number(request):
    content = request.GET
    group = content.get('group')
    group = int(group)

    created = datetime.datetime.now()
    batch_object = BatchNumberGroup.objects.create(group=group, created=created)
    print "batch_object", batch_object.batch_number

    #    batch_number = BatchNumberGroup.objects.get(group=group,created=created).batch_number
    #    print "batch_number1111111111",batch_number

    return HttpResponse(json.dumps({'bid': batch_object.pk, "batch_number": batch_object.batch_number}),
                        content_type="application/json")


def out_sid_batch(request):
    content = request.GET
    out_sid = content.get('out_sid')
    batch_number = content.get('batch_number')
    group = content.get('group')
    number = content.get('number')

    out_batch_object = BatchNumberOid.objects.create(out_sid=out_sid, batch_number=batch_number, group=group,
                                                     number=number, status=BatchNumberOid.ACTIVE)

    return HttpResponse(json.dumps({'bid': out_batch_object.pk}), content_type="application/json")


def drop_out_batch(request):
    content = request.GET
    out_sid = content.get('out_sid')
    BatchNumberOid.objects.get(out_sid=out_sid).delete()
    return HttpResponse(json.dumps({'out_sid': out_sid}), content_type="application/json")


@csrf_exempt
def merger_out_sid(request):
    content = request.GET
    batch_number = content.get("batch")

    out_sid_list = BatchNumberOid.objects.filter(batch_number=batch_number)
    print "len(out_sid_list)", out_sid_list.items
    a = ()
    b = ()
    for v in out_sid_list:
        b = (v.batch_number, v.out_sid)
        a.__add__(b)
    print 'aaaaaaaaaaaaaaaa', a
    return render_to_response('second_time_sort/merger_sort_out.html',
                              {"batch_number": batch_number,}, context_instance=RequestContext(request))

#                              
# def write_batch_outSid(batchNumber,out_sid,group):
#    batch_o,state = BatchNumberOid.objects.get_or_create(batch_number=batchNumber,out_sid=out_sid,group=group)
#    batch_o.save()
#
#    
# def batch_number_out(request):
#    content = request.POST
#    out_sid = content.get('outSid')
#    group   = content.get('group')
#    print "group%333333333333333333333333333333333333%%%%%",group
#    print "out_sid&&&333333333333333333333333333333333333333&&&&&",out_sid
#    return ''
