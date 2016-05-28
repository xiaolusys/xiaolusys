# coding=utf-8
import datetime
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from statistics import serializers
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import APIException
from statistics.models import SaleStats


class SaleStatsViewSet(viewsets.ModelViewSet):
    queryset = SaleStats.objects.all()
    serializer_class = serializers.StatsSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
