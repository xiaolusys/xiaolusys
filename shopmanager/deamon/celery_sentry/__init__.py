import logging
from celery.signals import task_failure
#from sentry.client.handlers import SentryHandler
from raven.contrib.django.handlers import SentryHandler

logger = logging.getLogger('sentry.errors')
logger.addHandler(SentryHandler())
def process_failure_signal(exception, traceback, sender, task_id,
                           signal, args, kwargs, einfo, **kw):
  exc_info = (type(exception), exception, traceback)
  logger.error(
    'Celery job exception: %s(%s)' % (exception.__class__.__name__, exception),
    exc_info=exc_info,
    extra={
      'data': {
        'task_id': task_id,
        'sender': sender,
        'args': args,
        'kwargs': kwargs,
      }
    }
  )
task_failure.connect(process_failure_signal)


  
