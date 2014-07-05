
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from .models import WXOrder,WXProduct,WXLogistic

@task
def pullWXOrderDuringTask():
    
    pass