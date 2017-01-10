# coding: utf8
from __future__ import absolute_import, unicode_literals


from django.core.management.base import BaseCommand

from flashsale.xiaolumm.tasks import task_fresh_elitemama_active_status


class Command(BaseCommand):

    def handle(self, *args, **options):

        task_fresh_elitemama_active_status()