# coding=utf-8
from __future__ import unicode_literals, absolute_import
from core.managers import BaseManager
import logging

logger = logging.getLogger(__name__)


class CustomerManager(BaseManager):
    @property
    def normal_customer(self):
        # type: () -> Optional[List[Customer]]
        queryset = super(CustomerManager, self).get_queryset()
        return queryset.filter(status=self.model.NORMAL).order_by('-created')
