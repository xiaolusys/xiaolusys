import djcelery
djcelery.setup_loader()

CELERY_INPORTS = ('task_daemon.manage.tasks',)
CELERY_RESULT_BACKEND = 'database'

BROKER_BACKEND = "djkombu.transport.DatabaseTransport"

EXECUTE_INTERVAL_TIME = 10*60

from datetime import timedelta
CELERYBEAT_SCHEDULE = {
    'runs-every-30-seconds':{
        'task':'task_daemon.manage.tasks.updateAllItemTask',
        'schedule':timedelta(seconds=EXECUTE_INTERVAL_TIME),
        'args':(),
    },
}

import logging
from celery.signals import task_failure
from sentry.client.handlers import SentryHandler

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