# coding=utf-8
from django.core.management.base import BaseCommand

from common.utils import update_model_fields
from flashsale.xiaolumm.models.models_fortune import AwardCarry


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        """
        acs = AwardCarry.objects.using('product').filter(uni_key__startswith='new_guy_task_subscribe_weixin_award_5_')

        if acs.count() > 1000:
            print 'wrong!!!', acs.count()
            return

        for i, ac in enumerate(acs):
            ac.carry_type = 8
            update_model_fields(ac, update_fields=['carry_type'])
            print i, ac.mama_id, ac.carry_type, ac.carry_description
