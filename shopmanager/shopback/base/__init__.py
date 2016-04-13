__author__ = 'meixqhi'
from django.contrib.auth.models import User
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.utils.functional import allow_lazy, SimpleLazyObject
import logging

logger = logging.getLogger('django.request')


def log_action(user_id, obj, action, msg):
    if isinstance(user_id, SimpleLazyObject):
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
        logger.error(exc.message, exc_info=True)
