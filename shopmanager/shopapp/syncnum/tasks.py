#-*- coding:utf8 -*-
import datetime
import json
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from django.db.models import Sum
from django.db import transaction
from auth.utils import format_datetime ,parse_datetime
from shopback import paramconfig as pcfg
from shopback.items.models import Item
from shopback.items.tasks import updateUserItemsTask,updateUserProductSkuTask,updateProductWaitPostNumTask
from shopback.orders.models import Order,Trade
from shopback.trades.models import MergeOrder
from shopback.users.models import User
from shopapp.syncnum.models import ItemNumTaskLog
from auth.utils import get_yesterday_interval_time
from auth import apis
import logging

logger = logging.getLogger('syncnum.handler')


        
        