import djcelery
djcelery.setup_loader()

CELERY_RESULT_BACKEND = 'database'

BROKER_BACKEND = "djkombu.transport.DatabaseTransport"

EXECUTE_INTERVAL_TIME = 10*60

EXECUTE_RANGE_TIME = 10*60

UPDATE_ITEM_NUM_INTERVAL = 5*60

from celery.schedules import crontab
from datetime import timedelta,datetime

CELERYBEAT_SCHEDULE = {
    'runs-every-10-minutes':{
        'task':'shopback.task.tasks.updateAllItemListTask',
        'schedule':timedelta(seconds=EXECUTE_INTERVAL_TIME),
        'args':(datetime.now(),),
    },
    'runs-every-day':{
        'task':'shopback.items.tasks.updateAllItemNumTask',
        'schedule':crontab(minute=0, hour=0),
        'args':(),
    },
    'runs-every-30-minutes':{
        'task':'search.tasks.updateItemKeywordsPageRank',
        'schedule':timedelta(seconds=120),#crontab(minute="*/30"),
        'args':()
    },
}


