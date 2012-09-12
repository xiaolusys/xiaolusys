#-*- encoding:utf8 -*-
import types
import json
from django.conf import settings
from django.core.cache import cache
from celery.task import task
from celery.registry import tasks
from celery.app.task import BaseTask



def single_instance_task(timeout,prefix=''):
    def task_exc(func):
        def delay(self, *args, **kwargs):
            return self.apply(args, kwargs)

        def decorate(*args, **kwargs):
            unique_mark = kwargs.get('unique_mark','')
            lock_id = "celery-single-instance-%s-%s"%(func.__name__,unique_mark)
            acquire_lock = lambda: cache.add(lock_id, "true", timeout)
            release_lock = lambda: cache.delete(lock_id)
            if acquire_lock():
                try:
                    return func(*args, **kwargs)
                finally:
                    release_lock()
            else :
                logger.error('the task %s is executing.'%func.__name__)
        result = task(name='%s%s' % (prefix,func.__name__))(decorate)
        if settings.DEBUG:
            result.delay = types.MethodType(delay, result)
        return result
    return task_exc



        
        