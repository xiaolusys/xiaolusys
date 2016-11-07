# coding=utf-8
import datetime
import django_filters
from operator import itemgetter
from itertools import groupby

from rest_framework import status
from rest_framework import authentication
from rest_framework import filters
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import exceptions

from ..models.activity import ActivityEntry
from ..serializers.activity import ActivitySerializer


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = ActivityEntry.objects.all()
    serializer_class = ActivitySerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser, permissions.DjangoModelPermissions)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    search_fields = ('=id', )

