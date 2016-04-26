# coding=utf-8
__author__ = 'meron'
from django.core.management.base import BaseCommand
from flashsale.pay.models import Customer
from flashsale.pay.models_user import genCustomerNickname
import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    def handle(self, *args, **options):
        cus = Customer.objects.filter(nick='')[:10]
        logger.debug('total customer:%s'%cus.count())
        cnt = 0
        for u in cus:
            u.nick = genCustomerNickname()
            u.save(update_fields=['nick'])
            cnt += 1
            if cnt % 5000 == 0:
                logger.debug('update customer number:%s' % cnt)

