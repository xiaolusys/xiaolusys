# coding=utf-8
import os, urlparse

from django.conf import settings
from django.forms import model_to_dict

from rest_framework.decorators import detail_route, list_route
from rest_framework import exceptions
from rest_framework import mixins
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import viewsets

from flashsale.promotion.models_top10 import TOP10ActivePic
from serializers import Top10PicModelSerializer


class Top10ViewSet(viewsets.ModelViewSet):
    queryset = TOP10ActivePic.objects.all()
    serializer_class = Top10PicModelSerializer
    # authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    # permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    @list_route(methods=['get'])
    def get_top10_by_activityid(self, request):
        content = request.REQUEST
        activity_id = content.get('activity_id', None)
        act_pics = self.queryset.filter(activity_id=activity_id).order_by("location_id")
        if act_pics:
            serializer = self.get_serializer(act_pics, many=True)
            return Response(serializer.data)
        else:
            return Response([])

    @list_route(methods=['post'])
    def save_pics(self, request):

        content = request.REQUEST
        arr = content.get("arr", None)
        act_id = content.get("act_id", None)
        data = eval(arr)  # json字符串转化

        TOP10ActivePic.objects.filter(activity_id=int(act_id)).delete()

        for da in data:
            activity_id = int(da['activity_id'])
            pic_type = int(da['pic_type'])
            model_id = int(da['model_id'])
            product_name = da['product_name']
            pic_path = da['pic_path']
            location_id = int(da['location_id'])
            pics = TOP10ActivePic.objects.create(activity_id=activity_id,
                                                 pic_type=pic_type,
                                                 model_id=model_id,
                                                 product_name=product_name,
                                                 pic_path=pic_path,
                                                 location_id=location_id)

            pics.save()
        return Response({"code": 0, "info": ""})
