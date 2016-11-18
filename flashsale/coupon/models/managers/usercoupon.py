# coding=utf-8
from __future__ import absolute_import, unicode_literals
import logging
from core.managers import BaseManager

logger = logging.getLogger(__name__)


class UserCouponManager(BaseManager):
    def get_query_set(self):
        _super = super(BaseManager, self)
        if hasattr(_super, 'get_query_set'):
            return _super.get_query_set()
        return _super.get_queryset()

    get_queryset = get_query_set
