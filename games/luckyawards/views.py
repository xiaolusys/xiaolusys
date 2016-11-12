# -*- coding:utf-8 -*-

from django.shortcuts import redirect
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework import renderers
from rest_framework.response import Response

from .models import Joiner

import logging

logger = logging.getLogger('django.request')


class LuckyAwardView(APIView):
    #     authentication_classes = (authentication.TokenAuthentication,)
    #     permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "awards/index.html"

    def get(self, request):
        joiners = Joiner.objects.filter(is_active=True)
        return Response({'joiners': joiners})

    def post(self, request):
        content = request.POST
        origin_url = content.get('origin_url')
        return redirect(origin_url)
