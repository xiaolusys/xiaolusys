import datetime
import json
from django.http import HttpResponse
from djangorestframework.views import ModelView
from djangorestframework.response import ErrorResponse
from djangorestframework import status
from .models import PrintAsyncTaskModel
from shopapp.asynctask.tasks import AsyncCategoryTask,AsyncOrderTask,PrintAsyncTask
from common.utils import parse_date


class AsyncCategoryView(ModelView):
    """ docstring for class AsyncCategoryView """

    def get(self, request, cids, *args, **kwargs):
        
        profile     = request.user.get_profile()
        content     = request.REQUEST
        seller_type = profile.type
        
        result = AsyncCategoryTask.delay(cids,profile.visitor_id,seller_type=seller_type)
        
        return {"task_id":result}
    
    post = get
    
    
class AsyncOrderView(ModelView):
    """ docstring for class AsyncOrderView """

    def get(self, request, start_dt, end_dt, *args, **kwargs):

        profile    = request.user.get_profile()
        content    = request.REQUEST
        
        start_dt   = parse_date(start_dt)
        end_dt     = parse_date(end_dt)

        result = AsyncOrderTask.delay(start_dt,end_dt,profile.visitor_id)

        return {"task_id":result}
    
    post = get
    
    
class AsyncInvoicePrintView(ModelView):
    """ docstring for class AsyncPrintView """

    def get(self, request, *args, **kwargs):

        profile    = request.user
        content    = request.REQUEST
        
        params =  {'trade_ids':content.get('trade_ids'),
                   'user_code':content.get('user_code')}
        task_model = PrintAsyncTaskModel.objects.create(
                                           task_type=PrintAsyncTaskModel.INVOICE,
                                           operator=profile.username,
                                           params=json.dumps(params))
        
        print_async_task = PrintAsyncTask.delay(task_model.pk)

        return {"task_id":print_async_task,"async_print_id":task_model.pk}
    
    post = get
    
    
class AsyncExpressPrintView(ModelView):
    """ docstring for class AsyncPrintView """

    def get(self, request, *args, **kwargs):

        profile    = request.user
        content    = request.REQUEST
        
        params =  {'trade_ids':content.get('trade_ids'),
                   'user_code':content.get('user_code')}
        task_model = PrintAsyncTaskModel.objects.create(
                                           task_type=PrintAsyncTaskModel.EXPRESS,
                                           operator=profile.username,
                                           params=json.dumps(params))
        
        print_async_task = PrintAsyncTask.delay(task_model.pk)

        return {"task_id":print_async_task,"async_print_id":task_model.pk}
    
    post = get
    
    