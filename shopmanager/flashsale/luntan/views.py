# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from flashsale.push.app_push import AppPush
from flashsale.protocol.constants import TARGET_SCHEMA,TARGET_PATHS
from rest_framework.response import Response
from django.http import HttpResponse

@login_required
def at_push(request,customer_id):
    if request.method == "POST":
        back_nickname = request.POST.get('back_nickname',None)
        comment_nickname = request.POST.get('comment_nickname',None)
        msg = back_nickname + "给" + comment_nickname + "回复一条评论"
        if comment_nickname and comment_nickname:
            AppPush.push(customer_id,TARGET_SCHEMA+TARGET_PATHS[13],msg)
            return HttpResponse({'customer-%d' % customer_id})
        else:
            HttpResponse({"parm erorr"})
    return HttpResponse({"method erorr"})

