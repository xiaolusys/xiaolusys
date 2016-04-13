from __future__ import unicode_literals
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import six
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status, exceptions
from rest_framework.compat import HttpResponseBase, View, set_rollback
from rest_framework.response import Response

import logging

logger = logging.getLogger('restapi.errors')


def my_exception_handler(exc, context):
    """
    Returns the response that should be used for any given exception.

    By default we handle the REST framework `APIException`, and also
    Django's built-in `Http404` and `PermissionDenied` exceptions.

    Any unhandled exceptions may return `None`, which will cause a 500 error
    to be raised.
    """
    if isinstance(exc, exceptions.APIException):
        headers = {}
        if getattr(exc, 'auth_header', None):
            headers['WWW-Authenticate'] = exc.auth_header
        if getattr(exc, 'wait', None):
            headers['Retry-After'] = '%d' % exc.wait

        if isinstance(exc.detail, (list, dict)):
            data = exc.detail
        else:
            data = {'detail': exc.detail}

        set_rollback()
        return Response(data, status=exc.status_code, headers=headers)

    elif isinstance(exc, Http404):
        msg = exc.message or _('Not found.')
        data = {'detail': six.text_type(msg)}

        set_rollback()
        return Response(data, status=status.HTTP_404_NOT_FOUND)

    elif isinstance(exc, PermissionDenied):
        msg = _('Permission denied.')
        data = {'detail': six.text_type(msg)}

        set_rollback()
        return Response(data, status=status.HTTP_403_FORBIDDEN)

    # Note: Unhandled exceptions will raise a 500 error.
    return None


def rest_exception(errmsg=''):
    def _func_wrapper(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
                err_msg = errmsg or exc.message or ''
                raise exceptions.APIException(err_msg)

        return _wrapper

    return _func_wrapper
