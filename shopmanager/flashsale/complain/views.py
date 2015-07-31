__author__ = 'timi06'
# coding:utf-8
# from django.http import HttpResponse, Http404
# from django.shortcuts import get_object_or_404
# from django.views.decorators.csrf import csrf_exempt
# from rest_framework.renderers import JSONRenderer
# from rest_framework.parsers import JSONParser
from .models import Complain
from .serializers import ComplainSerializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, mixins, generics, \
    viewsets, permissions, authentication, renderers

#
# class ComplainList(APIView):
#     """
#     列出所有complain数据，或创建一条新的complain数据。
#     """
#
#     def get(self, request, format=None):
#         complain = Complain.objects.all()
#         serializer = ComplainSerializers(complain, many=True)
#         return Response(serializer.data)
#
#     def post(self, request, format=None):
#         serializer = ComplainSerializers(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# class ComplainDetail(APIView):
#     """
#     检索，更新或删除数据。
#     """
#
#     def get_object(self, pk):
#         try:
#             return Complain.objects.get(id=pk)
#         except Complain.DoesNotExist:
#             raise Http404
#
#     def get(self, request, pk, format=None):
#         complain = self.get_object(pk)
#         serializer = ComplainSerializers(complain)
#         return Response(serializer.data)
#
#     def put(self, request, pk, format=None):
#         complain = self.get_object(pk)
#         serializer = ComplainSerializers(complain, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def delete(self, request, pk, format=None):
#         complain = self.get_object(pk)
#         complain.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
#
#
# class JSONResponse(HttpResponse):
#     """
#     HttpResponse呈现其内容为JSON。
#     """
#
#     def __init__(self, data, **kwargs):
#         content = JSONRenderer().render(data)
#         kwargs['content_type'] = 'application/json'
#         super(JSONResponse, self).__init__(content, **kwargs)
#
#
# @csrf_exempt
# def complain_list(request, format=None):
#     """
#     列出所有complain数据，或创建一条新的complain数据。
#     """
#     if request.method == 'GET':
#         complain = Complain.objects.all()
#         serializer = ComplainSerializers(complain, many=True)
#         return JSONResponse(serializer.data)
#
#     elif request.method == 'POST':
#         data = JSONParser().parse(request)
#         serializer = ComplainSerializers(data=data)
#         if serializer.is_valid():
#             serializer.save()
#             return JSONResponse(serializer.data, status=201)
#         return JSONResponse(serializer.errors, status=400)
#
#
# @csrf_exempt
# def complain_detail(request, pk, format=None):
#     """
#     检索，更新或删除数据。
#     """
#     try:
#         complain = Complain.objects.get(pk=pk)
#     except Complain.DoesNotExist:
#         return HttpResponse(status=404)
#
#     if request.method == 'GET':
#         serializer = ComplainSerializers(complain)
#         return JSONResponse(serializer.data)
#
#     elif request.method == 'PUT':
#         data = JSONParser().parse(request)
#         serializer = ComplainSerializers(Complain, data=data)
#         if serializer.is_valid():
#             serializer.save()
#             return JSONResponse(serializer.data)
#         return JSONResponse(serializer.errors, status=400)
#
#     elif request.method == 'DELETE':
#         complain.delete()
#         return HttpResponse(status=204)


# 显示数据列表，或创建数据
class ComplainList(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = Complain.objects.all()
    serializer_class = ComplainSerializers

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


# 检索，更新或删除数据
class ComplainDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                     generics.GenericAPIView):
    queryset = Complain.objects.all()
    serializer_class = ComplainSerializers

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

import permissions

# 创建数据，或显示数据列表
class ComplainsList(generics.ListCreateAPIView):
    """
    允许被查看或编辑
    """
    queryset = Complain.objects.all()
    serializer_class = ComplainSerializers
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAdminSuperUser, permissions.IsOwnerOrReadOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    queryset = Complain.objects.all()
    serializer_class = ComplainSerializers


# 检索，更新或删除数据
class ComplainsDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Complain.objects.all()
    serializer_class = ComplainSerializers


class ComplainViewSet(viewsets.ModelViewSet):
    """
    允许被组查看或编辑
    """
    queryset = Complain.objects.all()
    serializer_class = ComplainSerializers
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsOwnerOrReadOnly,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def create(self, request, *args, **kwargs):
        """
        创建投诉
        """
        insider_phone = request.user
        com_content = request.data['com_content']
        complain = Complain()
        complain.insider_phone = insider_phone
        complain.com_content = com_content
        complain.save()

        return Response("OK")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)