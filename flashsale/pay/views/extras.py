# coding:utf-8
from django.conf import settings

from rest_framework import permissions
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer
from rest_framework.views import APIView
from rest_framework.response import Response

from qiniu import Auth

class QiniuAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def get(self, request):
        access_key = settings.QINIU_ACCESS_KEY
        secret_key = settings.QINIU_SECRET_KEY
        bucket_name = "xiaolumm"

        q = Auth(access_key, secret_key)
        token = q.upload_token(bucket_name, expires=3600)
        return Response({'uptoken': token})