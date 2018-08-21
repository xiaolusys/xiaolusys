# coding=utf-8
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from rest_framework.response import Response

from rest_framework import authentication, viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import permissions

from flashsale.push.app_push import AppPush
from flashsale.protocol.constants import TARGET_SCHEMA, TARGET_PATHS

# @login_required
# def at_push(request,customer_id):
# if request.method == "POST":
#         back_nickname = request.POST.get('back_nickname',None)
#         comment_nickname = request.POST.get('comment_nickname',None)
#         msg = back_nickname + "给" + comment_nickname + "回复一条评论"
#         if comment_nickname and comment_nickname:
#             AppPush.push(customer_id,TARGET_SCHEMA+TARGET_PATHS[13],msg)
#             return HttpResponse({'customer-%d' % customer_id})
#         else:
#             HttpResponse({"parm erorr"})
#     return HttpResponse({"method erorr"})


class LuntanPushViewSet(viewsets.ViewSet):
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    @detail_route(methods=['post'])
    def at_push(self, request, pk):
        customer_id = pk
        back_nickname = request.POST.get('back_nickname', None)
        comment_nickname = request.POST.get('comment_nickname', None)
        # print back_nickname,comment_nickname
        # msg = str(back_nickname) + "给" + str(comment_nickname) + "回复一条评论"
        msg = str(back_nickname) + u"在小鹿论坛回复了你的评论,快点击来看看吧"
        if comment_nickname and comment_nickname:
            AppPush.push(int(customer_id), TARGET_SCHEMA + TARGET_PATHS[13], msg)
            return HttpResponse({'customer-%d' % int(customer_id)})
        else:
            return HttpResponse({"parm error"})