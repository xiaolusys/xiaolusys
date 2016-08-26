# coding=utf-8
import json
import datetime
from django.shortcuts import get_object_or_404
from django.forms import model_to_dict

from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from flashsale.pay.serializers.teambuy import TeamBuySerializer
from flashsale.pay.models import TeamBuy


class TeamBuyViewSet(viewsets.GenericViewSet, viewsets.mixins.RetrieveModelMixin):
    queryset = TeamBuy.objects.all()
    serializer_class = TeamBuySerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    # def retrieve(self, request, *args, **kwargs):
    #    return Response
