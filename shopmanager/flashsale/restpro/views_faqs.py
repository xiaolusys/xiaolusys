# coding=utf-8
from rest_framework import viewsets
from . import serializers
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.decorators import list_route
from rest_framework import exceptions
from flashsale.pay.models_faqs import SaleFaqs
from collections import OrderedDict


class SaleFaqsViewSet(viewsets.ModelViewSet):
    queryset = SaleFaqs.objects.all()
    serializer_class = serializers.SaleFaqsSerializer
    authentication_classes = ()
    permission_classes = ()
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def perform_update(self, serializer):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def get_question_type(self):
        """ 获取类型 (特别注意：在model中定义好的)"""
        types = self.queryset.values('question_type', 'detail_type').annotate().order_by('question_type')  # 需要排序
        question_types = OrderedDict()  # 注意这里使用了有序的字典
        # 先排序下类型元组
        QUESTION_TYPE = sorted(SaleFaqs.QUESTION_TYPE, key=lambda x: x[0])
        DETAIL_TYPE = sorted(SaleFaqs.DETAIL_TYPE, key=lambda x: x[0])
        for tu in types:
            if question_types.has_key(QUESTION_TYPE[tu['question_type']][1]):
                question_types[QUESTION_TYPE[tu['question_type']][1]].append(
                    {DETAIL_TYPE[tu['detail_type']][0]: DETAIL_TYPE[tu['detail_type']][1]})
            else:
                question_types[QUESTION_TYPE[tu['question_type']][1]] = [
                    {DETAIL_TYPE[tu['detail_type']][0]: DETAIL_TYPE[tu['detail_type']][1]}]
        return question_types

    @list_route(methods=['get'])
    def get_types(self, request):
        get_question_type = self.get_question_type()
        return Response(get_question_type)

    @list_route(methods=['get'])
    def get_question(self, request):
        content = request.REQUEST
        question_type = content.get("question_type")
        detail_type = content.get("detail_type")
        if question_type and detail_type:
            questions = self.queryset.filter(question_type=question_type,
                                             detail_type=detail_type).only('question', 'answer')
            serializer = self.get_serializer(questions, many=True)
            return Response({'code': 0, 'msg': 'ok', 'questions': serializer.data})
        else:
            return Response({'code': 1, 'msg': '类型出错', 'questions': ''})
