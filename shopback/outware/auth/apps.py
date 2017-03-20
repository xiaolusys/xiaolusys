# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class OutwareConfig(AppConfig):
    """Simple AppConfig which does not do automatic discovery."""

    name = 'outware.wareauth'
    verbose_name = "Outauth"

    def ready(self):
        pass
        # register signal listener


