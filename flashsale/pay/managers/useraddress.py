# coding=utf-8
from __future__ import unicode_literals, absolute_import
from core.managers import BaseManager
import logging

logger = logging.getLogger(__name__)


class NormalUserAddressManager(BaseManager):
    def get_queryset(self):
        queryset = super(NormalUserAddressManager, self).get_queryset()
        return queryset.filter(status=self.model.NORMAL).order_by('-created')
