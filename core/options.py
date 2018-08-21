# coding=utf-8
__author__ = 'imeron'
from django.contrib.auth.models import User
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType


def get_systemoa_user():
    user, state = User.objects.get_or_create(username='systemoa')
    return user


def log_action(user_id, obj, action, msg):
    if not isinstance(user_id, (int, long)):
        user_id = user_id.id
    try:
        LogEntry.objects.log_action(
            user_id=user_id,
            content_type_id=ContentType.objects.get_for_model(obj).id,
            object_id=obj.id,
            object_repr=repr(obj),
            change_message=msg,
            action_flag=action,
        )
    except Exception, exc:
        import logging
        logger = logging.getLogger('django.request')
        logger.error(exc.message, exc_info=True)
