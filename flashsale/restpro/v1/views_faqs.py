# coding=utf-8
from rest_framework import viewsets
from . import serializers
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.decorators import list_route
from rest_framework import exceptions
from flashsale.pay.models import FaqMainCategory, FaqsDetailCategory, SaleFaq


class SaleCategoryViewSet(viewsets.ModelViewSet):
    queryset = FaqMainCategory.objects.all()
    serializer_class = serializers.SaleFaqCategorySerializer
    authentication_classes = ()
    permission_classes = ()
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def list(self, request, *args, **kwargs):
        queryset = self.queryset
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def get_detail_category(self, request):
        """ 获取类型 (特别注意：在model中定义好的)"""
        content = request.GET
        main_category = content.get("main_category", None)
        details_category = FaqsDetailCategory.objects.filter(main_category_id=main_category)
        serializer = serializers.SaleFaqDetailCategorySerializer(details_category, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def get_question(self, request):
        content = request.GET
        main_category = content.get("main_category", None)
        detail_category = content.get("detail_category", None)
        questions = SaleFaq.objects.none()
        if main_category:
            questions = SaleFaq.objects.filter(main_category_id=main_category).only('question', 'answer')
        if main_category and detail_category:
            questions = SaleFaq.objects.filter(main_category_id=main_category,
                                               detail_category_id=detail_category).only('question', 'answer')
        page = self.paginate_queryset(questions)

        if page is not None:
            serializer = serializers.SaleFaqerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = serializers.SaleFaqerializer(questions, many=True)
        return Response({'code': 0, 'msg': 'ok', 'questions': serializer.data})

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def perform_update(self, serializer):
        raise exceptions.APIException('METHOD NOT ALLOWED')
