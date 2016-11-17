from __future__ import absolute_import, unicode_literals

import types
from django.conf import settings
from django.core.cache import cache
import logging


def single_instance_task(timeout, prefix=''):
    def task_exc(func):
        from shopmanager import celery_app as app

        def delay(self, *args, **kwargs):
            return self.apply(args, kwargs)

        def decorate(*args, **kwargs):
            lock_id = "celery-single-instance-" + func.__name__
            acquire_lock = lambda: cache.add(lock_id, "true", timeout)
            release_lock = lambda: cache.delete(lock_id)
            if acquire_lock():
                try:
                    return func(*args, **kwargs)
                finally:
                    release_lock()
            # else:
            #    logger = logging.getLogger('celery.handler')
            #    logger.error('the task %s is executing.' % func.__name__)

        result = task(name='%s%s' % (prefix, func.__name__))(decorate)
        if settings.DEBUG:
            result.delay = types.MethodType(delay, result)
        return result

    return task_exc


def single_record_task(timeout, prefix=''):
    def task_exc(func):
        from shopmanager import celery_app as app

        def delay(self, *args, **kwargs):
            return self.apply(args, kwargs)

        def decorate(*args, **kwargs):
            lock_id = "celery-single-instance-" + func.__name__ + func.param
            acquire_lock = lambda: cache.add(lock_id, "true", timeout)
            release_lock = lambda: cache.delete(lock_id)
            if acquire_lock():
                try:
                    return func(*args, **kwargs)
                finally:
                    release_lock()
            else:
                logger = logging.getLogger('celery.handler')
                logger.error('the task %s is executing.' % func.__name__)

        result = task(name='%s%s' % (prefix, func.__name__))(decorate)
        if settings.DEBUG:
            result.delay = types.MethodType(delay, result)
        return result

    return task_exc
