import djcelery
djcelery.setup_loader()

CELERY_RESULT_BACKEND = 'database'

BROKER_BACKEND = "djkombu.transport.DatabaseTransport"

EXECUTE_INTERVAL_TIME = 10*60

EXECUTE_RANGE_TIME = 6*60

from celery.schedules import crontab
from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    'runs-every-10-minutes':{
        'task':'shopback.task.tasks.updateAllItemListTask',
        'schedule':timedelta(seconds=EXECUTE_INTERVAL_TIME),
        'args':(),
    },
    'runs-every-day':{
        'task':'shopback.items.tasks.updateAllItemNumTask',
        'schedule':crontab(minute="*/1"),
        'args':(),
    },
}


