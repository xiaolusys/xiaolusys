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
            if resp and resp.get('object'):
                code = action_code
                if resp.get('action_code') is not None:
                    code = resp.get('action_code')
                log_ware_action(
                    resp.get('object'),
                    code,
                    state_code=resp.get('success') and constants.GOOD or constants.ERROR,
                    message=resp.get('message')
                )
            return resp
        return _wrapper
    return _func
