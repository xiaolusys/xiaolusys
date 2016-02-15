# coding:utf-8
__author__ = 'imeron'
import re
import json
import urllib
from django.conf import settings
from django.contrib.admin.models import LogEntry,User, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType


def log_action(user_id,obj,action,msg):
    try:
        LogEntry.objects.log_action(
                user_id = user_id,
                content_type_id = ContentType.objects.get_for_model(obj).id,
                object_id = obj.id,
                object_repr = repr(obj),
                change_message = msg,
                action_flag = action,
            )
    except Exception,exc:
        import logging 
        logger =  logging.getLogger('django.request')
        logger.error(exc.message,exc_info=True)


