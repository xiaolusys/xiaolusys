# coding: utf8
from __future__ import absolute_import, unicode_literals

from .models.base import log_ware_action
from . import constants

import logging
logger = logging.getLogger(__name__)

def action_decorator(action_code):
    """ 记录action　的日志 """
    def _func(func):
        def _wrapper(*args, **kwargs):
            resp = func(*args, **kwargs)
            if resp.get('object'):
                log_ware_action(
                    resp.get('object'),
                    action_code,
                    state_code=resp.get('success', constants.ERROR),
                    message=resp.get('message')
                )
            return resp
        return _wrapper
    return _func
