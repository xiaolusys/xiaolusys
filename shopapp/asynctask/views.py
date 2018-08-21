import datetime
import json

from .models import PrintAsyncTaskModel
from shopapp.asynctask import tasks
from common.utils import parse_date

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer
from rest_framework.views import APIView
from rest_framework import filters
from rest_framework import authentication
from . import serializers


class AsyncCategoryView(APIView):
    """ docstring for class AsyncCategoryView """
    serializer_class = serializers.PrintAsyncTaskModeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)

    # print "start3333"
    def get(self, request, cids, *args, **kwargs):
        profile = request.user.get_profile()
        seller_type = profile.type
        result = tasks.AsyncCategoryTask.delay(cids, profile.visitor_id, seller_type=seller_type)

        return Response({"task_id": result})

    post = get


class AsyncOrderView(APIView):
    """ docstring for class AsyncOrderView """
    serializer_class = serializers.PrintAsyncTaskModeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)

    def get(self, request, start_dt, end_dt, *args, **kwargs):
        profile = request.user.get_profile()

        start_dt = parse_date(start_dt)
        end_dt = parse_date(end_dt)

        result = tasks.task_async_order.delay(start_dt, end_dt, profile.visitor_id)
        return Response({"task_id": result})

    post = get


class AsyncInvoicePrintView(APIView):
    """ docstring for class AsyncPrintView """
    serializer_class = serializers.PrintAsyncTaskModeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (TemplateHTMLRenderer, BrowsableAPIRenderer)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    template_name = "asynctask/async_print_commit.html"

    # print "start   AsyncInvoicePrintView"
    def get(self, request, *args, **kwargs):

        profile = request.user
        content = request.GET

        params = {'trade_ids': content.get('trade_ids'),
                  'user_code': content.get('user_code')}
        task_model = PrintAsyncTaskModel.objects.create(
            task_type=PrintAsyncTaskModel.INVOICE,
            operator=profile.username,
            params=json.dumps(params))

        from shopapp.asynctask.tasks import task_print_async
        print_async_task = task_print_async.delay(task_model.pk)

        return Response({"task_id": print_async_task, "async_print_id": task_model.pk})

    post = get

class AsyncInvoice2PrintView(APIView):
    """ docstring for class AsyncPrintView """
    serializer_class = serializers.PrintAsyncTaskModeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (TemplateHTMLRenderer, BrowsableAPIRenderer)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    template_name = "asynctask/async_print_commit.html"

    # print "start   AsyncInvoicePrintView"
    def get(self, request, *args, **kwargs):

        profile = request.user
        content = request.GET

        params = {'trade_ids': content.get('trade_ids'),
                  'user_code': content.get('user_code')}
        task_model = PrintAsyncTaskModel.objects.create(
            task_type=PrintAsyncTaskModel.INVOICE,
            operator=profile.username,
            params=json.dumps(params))

        print_async_task = tasks.task_print_async2.delay(task_model.pk)

        return Response({"task_id": print_async_task, "async_print_id": task_model.pk})


class AsyncExpressPrintView(APIView):
    """ docstring for class AsyncPrintView """
    serializer_class = serializers.PrintAsyncTaskModeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (TemplateHTMLRenderer, BrowsableAPIRenderer)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    template_name = "asynctask/async_print_commit.html"

    def get(self, request, *args, **kwargs):
        profile = request.user
        content = request.GET

        params = {'trade_ids': content.get('trade_ids'),
                  'user_code': content.get('user_code')}
        task_model = PrintAsyncTaskModel.objects.create(
            task_type=PrintAsyncTaskModel.EXPRESS,
            operator=profile.username,
            params=json.dumps(params))

        print_async_task = tasks.task_print_async.delay(task_model.pk)

        return Response({"task_id": print_async_task, "async_print_id": task_model.pk})

    post = get
