# coding: utf8
from __future__ import absolute_import, unicode_literals


from django.core.management.base import BaseCommand
import datetime
import logging
from core.options import get_systemoa_user
from core.options import log_action, CHANGE
from flashsale.xiaolumm.models import XiaoluMama
from flashsale.xiaolumm.tasks import task_fresh_elitemama_active_status

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):

        # task_fresh_elitemama_active_status()
        now = datetime.datetime.now()
        sys_oa = get_systemoa_user()

        effect_elite_mms = XiaoluMama.objects.filter(
            status=XiaoluMama.EFFECT,
            last_renew_type=XiaoluMama.SCAN)
        for emm in effect_elite_mms.iterator():
            try:
                emm.status = XiaoluMama.FROZEN
                emm.save(update_fields=['status'])
                log_action(sys_oa, emm, CHANGE, u'schedule task: renew timeout,chg to frozen')
            except TypeError as e:
                logger.error(u" FROZEN mama:%s, error info: %s" % (emm.id, e))
