# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class PayConfig(AppConfig):
    """Simple AppConfig which does not do automatic discovery."""

    name = 'flashsale.pay'
    verbose_name = "Pay"

    def ready(self):

        # register signal listener
        from . import listeners

