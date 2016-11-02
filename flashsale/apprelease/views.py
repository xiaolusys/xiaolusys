# coding=utf-8
import datetime
from django.shortcuts import render, redirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from rest_framework import permissions, authentication, renderers
from rest_framework.views import APIView
from rest_framework.response import Response
import constants

from flashsale.apprelease import serializers
from .models import AppRelease

import logging

logger = logging.getLogger(__name__)


class addNewReleaseView(APIView):
    """
    上传app新版本到七牛，跟换后台版本
    """
    template = constants.ADMIN_NEW_RELEASE_VERSION
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (renderers.BrowsableAPIRenderer,)

    def get(self, request):
        response = render_to_response(self.template, {}, context_instance=RequestContext(request))
        return response

    def post(self, request):
        content = request.REQUEST
        download_link = content.get('download_link', None)
        version = content.get('version', None)
        release_time = content.get('release_time', None)
        qrcode_link = content.get('qrcode_link', None)
        version_code = content.get('version_code', None)
        hash_value = content.get('hash_value', None)
        memo = content.get('memo', None)
        now = datetime.datetime.now()
        release_time = datetime.datetime.strptime(release_time, '%Y-%m-%d %H:%M:%S') if release_time else now
        old_rel = AppRelease.objects.all().order_by('-release_time').first()
        if old_rel:
            before_release_time = old_rel.release_time
            if release_time < before_release_time:
                message = '存在版本号为{0}发布时间为{1},该时间大于{2},不予发布！'.format(old_rel.version, before_release_time, release_time)
                return render_to_response(self.template, {"message": message,
                                                          "download_link": download_link,
                                                          "qrcode_link": qrcode_link},
                                          context_instance=RequestContext(request))
            if old_rel.version == version or old_rel.hash_value == hash_value:
                message = '版本号{0}已经存在！'.format(old_rel.version)
                return render_to_response(self.template, {"message": message,
                                                          "download_link": download_link,
                                                          "qrcode_link": qrcode_link},
                                          context_instance=RequestContext(request))
        app = AppRelease(
            download_link=download_link,
            qrcode_link=qrcode_link,
            release_time=release_time,
            memo=memo,
            hash_value=hash_value,
            version=version,
            version_code=version_code
        )
        app.save()
        return redirect(constants.RELESE_SUCCESS_PAGE)


class AppReleaseView(APIView):
    renderer_classes = (renderers.JSONRenderer, )

    def get(self, request):
        app = AppRelease.objects.filter(status=AppRelease.VALID,device_type=AppRelease.DEVICE_ANDROID).order_by('-release_time').first()
        if not app:
            logger.error(u'get_newest_app_release bug no app release found')
        serializer = serializers.AppReleaseSerialize(app)

        return Response(serializer.data)
