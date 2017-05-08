# coding=utf-8
from django.core.management.base import BaseCommand

from common.utils import update_model_fields
from flashsale.xiaolumm.models.models_fortune import AwardCarry


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        """
        from flashsale.coupon.apis.v1.transfer import get_transfer_record_by_id, agree_apply_transfer_record_2_sys
        record = get_transfer_record_by_id(120216)
        agree_apply_transfer_record_2_sys(record)
